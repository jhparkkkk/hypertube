import React, { useState, useEffect, useRef, useCallback } from 'react';
import { debounce } from 'lodash';
import {
  Box,
  Grid,
  TextField,
  CircularProgress,
} from '@mui/material';
import { api } from '../../api/axiosConfig';
import { Movie } from './shared/types';
import { MovieCard } from './shared/components';

const MovieLibrary: React.FC = () => {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const observer = useRef<IntersectionObserver>();

  const lastMovieElementRef = useCallback((node: HTMLElement | null) => {
    if (loading) return;
    if (observer.current) observer.current.disconnect();
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore) {
        setPage(prevPage => prevPage + 1);
      }
    });
    if (node) observer.current.observe(node);
  }, [loading, hasMore]);

  const fetchMovies = async (searchTerm: string, currentPage: number) => {
    setLoading(true);
    try {
      const response = await api.get('/movies/', {
        params: {
          search: searchTerm,
          page: currentPage
        }
      });
      
      const moviesData = Array.isArray(response.data) ? response.data : response.data.results;
      const totalPages = Array.isArray(response.data) ? Math.ceil(response.data.length / 20) : response.data.total_pages;
      
      if (moviesData) {
        setMovies(prev => 
          currentPage === 1 ? moviesData : [...prev, ...moviesData]
        );
        setHasMore(currentPage < totalPages);
      } else {
        setMovies([]);
        setHasMore(false);
      }
    } catch (error) {
      console.error('Error fetching movies:', error);
      setMovies([]);
      setHasMore(false);
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
  }, [search]);

  useEffect(() => {
    if (page > 1) {
      fetchMovies(search, page);
    }
  }, [page]);

  return (
    <Box sx={{ p: 3, backgroundColor: '#1a1a1a', minHeight: '100vh' }}>
      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Search movies"
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
      </Box>

      <Grid container spacing={3}>
        {movies.map((movie, index) => (
          <Grid
            item
            xs={12}
            sm={6}
            md={4}
            lg={3}
            key={`${movie.id}-${index}`}
            ref={index === movies.length - 1 ? lastMovieElementRef : null}
          >
            <MovieCard movie={movie} />
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