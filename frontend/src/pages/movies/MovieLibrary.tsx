import React, { useState, useEffect, useRef, useCallback } from 'react';
import { debounce } from 'lodash';
import {
	Box,
	Grid,
	TextField,
	CircularProgress,
	Typography,
	FormControl,
	InputLabel,
	Select,
	MenuItem,
	SelectChangeEvent,
	Rating,
} from '@mui/material';
import { api } from '../../api/axiosConfig';
import { Movie } from './shared/types';
import { MovieCard } from './shared/components';

interface MovieResponse {
	results: Movie[];
	page: number;
	total_pages: number;
}

const MovieLibrary: React.FC = () => {
	const [movies, setMovies] = useState<Movie[]>([]);
	const [search, setSearch] = useState<string>('');
	const [loading, setLoading] = useState<boolean>(false);
	const [page, setPage] = useState<number>(1);
	const [hasMore, setHasMore] = useState<boolean>(true);
	const [genre, setGenre] = useState<string>('');
	const [rating, setRating] = useState<string>('');
	const [year, setYear] = useState<string>('');
	const [, setTotalResults] = useState<number>(0);
	const observer = useRef<IntersectionObserver | null>(null);

	const [watchedMovieIds, setWatchedMovieIds] = useState<number[]>([]);

	const fetchWatchHistory = async () => {
		try {
			const response = await api.get('/history/');
			const ids = response.data.map((entry: any) => entry.tmdb_id);
			console.log('Fetched watched movie IDs:', ids);
			console.log('Fetched watch history:', response.data);
			setWatchedMovieIds(ids);
		} catch (error) {
			console.error('Error fetching watch history:', error);
		}
	};


	const genres = [
		'Action', 'Adventure', 'Animation', 'Comedy', 'Documentary', 'Drama',
		'Family', 'Fantasy', 'History', 'Horror', 'Music', 'Mystery',
		'Romance', 'Science Fiction', 'TV Movie', 'Thriller', 'War', 'Western'
	];

	const currentYear = new Date().getFullYear();
	const years = Array.from({ length: 50 }, (_, i) => (currentYear - i).toString());

	const lastMovieElementRef = useCallback((node: HTMLElement | null) => {
		if (loading) return;
		if (observer.current) observer.current.disconnect();
		observer.current = new IntersectionObserver(entries => {
			if (entries[0].isIntersecting && hasMore) {
				setPage((prevPage: number) => prevPage + 1);
			}
		});
		if (node) observer.current.observe(node);
	}, [loading, hasMore]);

	const fetchMovies = async (searchTerm: string, currentPage: number) => {
		setLoading(true);
		try {
			const response = await api.get<MovieResponse>('/movies/', {
				params: {
					query: searchTerm,
					page: currentPage,
					genre: genre || undefined,
					year: year || undefined,
					rating: rating || undefined
				}
			});

			const { results: moviesData, total_pages: totalPages } = response.data;

			if (moviesData) {
				// Filter out movies without posters (backend should already do this)
				const validMovies = moviesData.filter((movie: Movie) => movie.poster_path);

				setMovies((prev: Movie[]) =>
					currentPage === 1 ? validMovies : [...prev, ...validMovies]
				);
				console.log('Fetched movies:', validMovies);
				setHasMore(currentPage < totalPages);
				setTotalResults(validMovies.length);
			} else {
				setMovies([]);
				setHasMore(false);
				setTotalResults(0);
			}
		} catch (error) {
			console.error('Error fetching movies:', error);
			setMovies([]);
			setHasMore(false);
			setTotalResults(0);
		}
		setLoading(false);
	};

	const debouncedSearch = useCallback(
		debounce((searchTerm: string) => {
			setPage(1);
			fetchMovies(searchTerm, 1);
		}, 500),
		[]
	);

	useEffect(() => {
		debouncedSearch(search);
		return () => debouncedSearch.cancel();
	}, [search, debouncedSearch]);

	useEffect(() => {
		if (page > 1) {
			fetchMovies(search, page);
		}
	}, [page, search]);

	useEffect(() => {
		fetchWatchHistory();
		setPage(1);
		fetchMovies(search, 1);
	}, [genre, year, rating]);

	const handleGenreChange = (event: SelectChangeEvent) => {
		setGenre(event.target.value);
	};

	const handleYearChange = (event: SelectChangeEvent) => {
		setYear(event.target.value);
	};

	return (
		<Box sx={{ p: 3, backgroundColor: '#1a1a1a', minHeight: '100vh' }}>
			<Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
				<TextField
					fullWidth
					placeholder="Search movies..."
					variant="outlined"
					value={search}
					onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearch(e.target.value)}
					sx={{
						maxWidth: 600,
						'& .MuiOutlinedInput-root': {
							backgroundColor: '#2a2a2a',
							color: 'white',
							'& fieldset': {
								borderColor: '#444',
							},
							'&:hover fieldset': {
								borderColor: '#666',
							},
							'&.Mui-focused fieldset': {
								borderColor: '#888',
							},
						},
						'& .MuiOutlinedInput-input::placeholder': {
							color: '#888',
						},
					}}
				/>

				<FormControl sx={{ minWidth: 200 }}>
					<InputLabel sx={{ color: '#888' }}>Genre</InputLabel>
					<Select
						value={genre}
						label="Genre"
						onChange={handleGenreChange}
						sx={{
							backgroundColor: '#2a2a2a',
							color: 'white',
							'& .MuiOutlinedInput-notchedOutline': {
								borderColor: '#444',
							},
							'&:hover .MuiOutlinedInput-notchedOutline': {
								borderColor: '#666',
							},
							'&.Mui-focused .MuiOutlinedInput-notchedOutline': {
								borderColor: '#888',
							},
						}}
					>
						<MenuItem value="">All Genres</MenuItem>
						{genres.map((g) => (
							<MenuItem key={g} value={g}>{g}</MenuItem>
						))}
					</Select>
				</FormControl>

				<FormControl sx={{ minWidth: 200 }}>
					<InputLabel sx={{ color: '#888' }}>Year</InputLabel>
					<Select
						value={year}
						label="Year"
						onChange={handleYearChange}
						sx={{
							backgroundColor: '#2a2a2a',
							color: 'white',
							'& .MuiOutlinedInput-notchedOutline': {
								borderColor: '#444',
							},
							'&:hover .MuiOutlinedInput-notchedOutline': {
								borderColor: '#666',
							},
							'&.Mui-focused .MuiOutlinedInput-notchedOutline': {
								borderColor: '#888',
							},
						}}
					>
						<MenuItem value="">All Years</MenuItem>
						{years.map((y) => (
							<MenuItem key={y} value={y}>{y}</MenuItem>
						))}
					</Select>
				</FormControl>

				<Box sx={{ display: 'flex', alignItems: 'center', minWidth: 200 }}>
					<Typography sx={{ color: '#888', mr: 1 }}>Min Rating</Typography>
					<Rating
						name="rating-filter"
						value={Number(rating) / 2}
						precision={0.5}
						onChange={(_, newValue) => setRating(newValue ? String(newValue * 2) : '')}
						sx={{
							color: '#ffb400',
							'& .MuiRating-iconEmpty': { color: '#444' },
						}}
					/>
				</Box>
			</Box>

			{movies.length === 0 && !loading && (
				<Typography variant="h6" color="white" align="center" sx={{ mt: 4 }}>
					{search ? 'No movies found' : 'Loading popular movies...'}
				</Typography>
			)}

			<Grid container spacing={3}>
				{movies.map((movie: Movie, index: number) => (
					<Grid
						item
						xs={12}
						sm={6}
						md={4}
						lg={3}
						key={`${movie.id}-${index}`}
						ref={index === movies.length - 1 ? lastMovieElementRef : null}
					>
						<MovieCard movie={movie} watched={watchedMovieIds.includes(movie.id)} />

					</Grid>
				))}
			</Grid>

			{loading && (
				<Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
					<CircularProgress sx={{ color: 'white' }} />
				</Box>
			)}
		</Box>
	);
};

export default MovieLibrary; 