import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
	Box,
	Typography,
	Grid,
	Paper,
	Rating,
	Chip,
	Divider,
	List,
	ListItem,
	ListItemText,
} from '@mui/material';
import { api } from '../../api/axiosConfig';
import MoviePlayer from './MoviePlayer';
import MovieComments from './MovieComments';

interface Genre {
	id: number;
	name: string;
}

interface ProductionCompany {
	id: number;
	name: string;
	logo_path: string | null;
	origin_country: string;
}

interface ProductionCountry {
	iso_3166_1: string;
	name: string;
}

interface SpokenLanguage {
	english_name: string;
	iso_639_1: string;
	name: string;
}

interface Subtitle {
	language_code: string;
	language_name: string;
	name: string;
}

interface Movie {
	id: number;
	title: string;
	original_title: string;
	overview: string;
	release_date: string;
	runtime: number;
	vote_average: number;
	vote_count: number;
	popularity: number;
	poster_path: string | null;
	backdrop_path: string | null;
	genres: Genre[];
	production_companies: ProductionCompany[];
	production_countries: ProductionCountry[];
	spoken_languages: SpokenLanguage[];
	available_subtitles: Subtitle[];
	comments_count: number;
	budget: number;
	revenue: number;
	status: string;
	tagline: string;
	imdb_id: string | null;
	magnet_link?: string;
	adult: boolean;
}

const MovieDetails: React.FC = () => {
	const { id } = useParams<{ id: string }>();
	const [movie, setMovie] = useState<Movie | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		const fetchMovieDetails = async () => {
			try {
				const response = await api.get(`/movies/${id}/`);
				setMovie(response.data);

				// If magnet link exists, start the stream automatically
				if (response.data.magnet_link) {
					try {
						await api.post(`/video/${id}/start/`, {
							magnet_link: response.data.magnet_link
						});
						await api.post(`/history/${id}/`);
					} catch (error) {
						console.error('Error starting stream:', error);
					}
				}
			} catch (error) {
				console.error('Error fetching movie details:', error);
				setError('Failed to load movie details');
			} finally {
				setLoading(false);
			}
		};

		fetchMovieDetails();
	}, [id]);

	if (loading) {
		return (
			<Box sx={{
				display: 'flex',
				justifyContent: 'center',
				alignItems: 'center',
				minHeight: '100vh',
				backgroundColor: '#1a1a1a'
			}}>
				<Typography variant="h6" color="white">Loading...</Typography>
			</Box>
		);
	}

	if (error || !movie) {
		return (
			<Box sx={{
				p: 3,
				backgroundColor: '#1a1a1a',
				minHeight: '100vh',
				color: 'white'
			}}>
				<Typography variant="h5">{error || 'Movie not found'}</Typography>
			</Box>
		);
	}

	const formatCurrency = (amount: number): string => {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			maximumFractionDigits: 0,
		}).format(amount);
	};

	const formatRuntime = (minutes: number): string => {
		const hours = Math.floor(minutes / 60);
		const remainingMinutes = minutes % 60;
		return `${hours}h ${remainingMinutes}m`;
	};

	const options: Intl.DateTimeFormatOptions = {
		year: 'numeric',
		month: 'long',
		day: 'numeric'
	};
	const formattedDate: string = new Date(movie.release_date).toLocaleDateString(undefined, options);
	console.log(formattedDate);

	return (
		<Box sx={{ backgroundColor: '#1a1a1a', minHeight: '100vh', color: 'white' }}>
			{movie.backdrop_path && (
				<Box
					sx={{
						height: '400px',
						width: '100%',
						position: 'relative',
						backgroundImage: `linear-gradient(to bottom, rgba(26,26,26,0) 0%, rgba(26,26,26,1) 100%), 
                             url(https://image.tmdb.org/t/p/original${movie.backdrop_path})`,
						backgroundSize: 'cover',
						backgroundPosition: 'center',
					}}
				/>
			)}

			<Box sx={{ p: 3, mt: movie.backdrop_path ? -20 : 0 }}>
				<Grid container spacing={4}>
					<Grid item xs={12} md={4}>
						<Paper
							elevation={3}
							sx={{
								overflow: 'hidden',
								backgroundColor: '#2a2a2a',
								border: '1px solid #444'
							}}
						>
							<img
								src={movie.poster_path
									? `https://image.tmdb.org/t/p/w500${movie.poster_path}`
									: '/placeholder.jpg'
								}
								alt={movie.title}
								style={{ width: '100%', height: 'auto' }}
							/>
						</Paper>

						<Box sx={{ mt: 3, backgroundColor: '#2a2a2a', p: 2, borderRadius: 1 }}>
							<List dense>
								{movie.runtime > 0 && (
									<ListItem>
										<ListItemText
											primary="Runtime"
											secondary={formatRuntime(movie.runtime)}
											secondaryTypographyProps={{ sx: { color: '#ddd' } }}
										/>
									</ListItem>
								)}
								{movie.budget > 0 && (
									<ListItem>
										<ListItemText
											primary="Budget"
											secondary={formatCurrency(movie.budget)}
											secondaryTypographyProps={{ sx: { color: '#ddd' } }}
										/>
									</ListItem>
								)}
								{movie.revenue > 0 && (
									<ListItem>
										<ListItemText
											primary="Revenue"
											secondary={formatCurrency(movie.revenue)}
											secondaryTypographyProps={{ sx: { color: '#ddd' } }}
										/>
									</ListItem>
								)}
								{movie.release_date && (
									<ListItem>
										<ListItemText
											primary="Release Date"
											secondary={formattedDate}
											secondaryTypographyProps={{ sx: { color: '#ddd' } }}
										/>
									</ListItem>
								)}
								{movie.imdb_id && (
									<ListItem>
										<ListItemText
											primary="IMDB"
											secondary={
												<a
													href={`https://www.imdb.com/title/${movie.imdb_id}`}
													target="_blank"
													rel="noopener noreferrer"
													style={{ color: '#f5c518' }}
												>
													View on IMDB
												</a>
											}
										/>
									</ListItem>
								)}
							</List>
						</Box>
					</Grid>

					<Grid item xs={12} md={8}>
						<Typography variant="h4" gutterBottom sx={{
							fontWeight: 500,
							textShadow: '2px 2px 4px rgba(0,0,0,0.5)'
						}}>
							{movie.title}
							{movie.original_title !== movie.title && (
								<Typography
									variant="subtitle1"
									sx={{ color: '#888', mt: 1 }}
								>
									Original title: {movie.original_title}
								</Typography>
							)}
						</Typography>

						{movie.tagline && (
							<Typography
								variant="subtitle1"
								sx={{
									color: '#888',
									fontStyle: 'italic',
									mb: 2
								}}
							>
								{movie.tagline}
							</Typography>
						)}

						<Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
							<Rating
								value={movie.vote_average / 2}
								precision={0.5}
								readOnly
								sx={{
									color: '#f5c518',
									'& .MuiRating-icon': {
										fontSize: '1.2rem'
									}
								}}
							/>
							<Typography variant="body2" sx={{ color: '#888' }}>
								{movie.vote_average.toFixed(1)} ({movie.vote_count.toLocaleString()} votes)
							</Typography>
							<Divider orientation="vertical" flexItem sx={{ bgcolor: '#444' }} />
							<Typography variant="body1" sx={{ color: '#888' }}>
								{new Date(movie.release_date).getFullYear()}
							</Typography>
							{movie.adult && (
								<Chip
									label="18+"
									size="small"
									sx={{
										bgcolor: '#dc3545',
										color: 'white'
									}}
								/>
							)}
						</Box>

						<Box sx={{ mb: 3 }}>
							{movie.genres.map((genre: Genre) => (
								<Chip
									key={genre.id}
									label={genre.name}
									sx={{
										mr: 1,
										mb: 1,
										bgcolor: '#333',
										color: 'white',
										'&:hover': {
											bgcolor: '#444'
										}
									}}
								/>
							))}
						</Box>

						<Typography
							variant="body1"
							paragraph
							sx={{
								fontSize: '1.1rem',
								lineHeight: 1.7,
								color: '#ddd',
								maxWidth: '800px'
							}}
						>
							{movie.overview}
						</Typography>

						{movie.production_companies.length > 0 && (
							<Box sx={{ mt: 4 }}>
								<Typography variant="h6" gutterBottom>Production Companies</Typography>
								<Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
									{movie.production_companies.map((company: ProductionCompany) => (
										<Chip
											key={company.id}
											label={company.name}
											sx={{
												bgcolor: '#333',
												color: 'white',
											}}
										/>
									))}
								</Box>
							</Box>
						)}

						{movie.available_subtitles.length > 0 && (
							<Box sx={{ mt: 4 }}>
								<Typography variant="h6" gutterBottom>Available Subtitles</Typography>
								<Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
									{movie.available_subtitles.map((subtitle: Subtitle) => (
										<Chip
											key={subtitle.language_code}
											label={subtitle.language_name}
											size="small"
											sx={{
												bgcolor: '#333',
												color: 'white',
											}}
										/>
									))}
								</Box>
							</Box>
						)}
					</Grid>
				</Grid>

				{movie.magnet_link && (
					<Paper
						elevation={3}
						sx={{
							mt: 4,
							p: 2,
							backgroundColor: '#2a2a2a',
							border: '1px solid #444',
							borderRadius: 2
						}}
					>
						<Typography
							variant="h5"
							gutterBottom
							sx={{
								color: '#fff',
								mb: 2,
								fontWeight: 500
							}}
						>
						</Typography>
						<MoviePlayer movieId={Number(id)} magnet={movie.magnet_link} />
					</Paper>
				)}

				<MovieComments movieId={Number(id)} commentsCount={movie.comments_count} />
			</Box>
		</Box>
	);
};

export default MovieDetails; 