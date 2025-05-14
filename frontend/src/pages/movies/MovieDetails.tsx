import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Rating,
} from '@mui/material';
import { api } from '../../api/axiosConfig';
import MoviePlayer from './MoviePlayer';
import MovieComments from './MovieComments';

interface Movie {
  id: number;
  title: string;
  overview: string;
  release_date: string;
  vote_average: number;
  poster_path: string | null;
  backdrop_path: string | null;
  magnet_link?: string;
}

const MovieDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [movie, setMovie] = useState<Movie | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isStartingStream, setIsStartingStream] = useState(false);

  useEffect(() => {
    const fetchMovieDetails = async () => {
      try {
        const response = await api.get(`/movies/${id}/`);
        setMovie(response.data);
        
        // If magnet link exists, start the stream automatically
        if (response.data.magnet_link) {
          // setIsStartingStream(true);
          try {
            await api.post(`/video/${id}/start/`, {
              magnet_link: response.data.magnet_link
            });
						await api.post(`/history/${id}/`);
          } catch (error) {
            console.error('Error starting stream:', error);
          }
          // setIsStartingStream(false);
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
          </Grid>

          <Grid item xs={12} md={8}>
            <Typography variant="h4" gutterBottom sx={{ 
              fontWeight: 500,
              textShadow: '2px 2px 4px rgba(0,0,0,0.5)'
            }}>
              {movie.title}
            </Typography>

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
              <Typography variant="body1" sx={{ color: '#888' }}>
                {new Date(movie.release_date).getFullYear()}
              </Typography>
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
              Watch Movie
            </Typography>
            <MoviePlayer movieId={Number(id)} magnet={movie.magnet_link} />
          </Paper>
        )}
				<MovieComments movieId={Number(id)} />
      </Box>
    </Box>
  );
};

export default MovieDetails; 