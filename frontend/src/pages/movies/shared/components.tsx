import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardMedia,
  CardContent,
  Typography,
  Rating,
} from '@mui/material';
import { MovieCardProps } from './types';
import { movieCardStyles } from './styles';

export const MovieCard: React.FC<MovieCardProps> = ({ movie, watched }) => {
  const navigate = useNavigate();
  const [imageError, setImageError] = useState(false);
  const year = movie.release_date ? new Date(movie.release_date).getFullYear() : '';
  const posterUrl = !imageError && movie.poster_path 
    ? `https://image.tmdb.org/t/p/w500${movie.poster_path}`
    : '';

  return (
    <Card 
      sx={{
        ...movieCardStyles.card,
        position: 'relative',
        overflow: 'hidden',
        cursor: 'pointer',
      }}
      onClick={() => navigate(`/movies/${movie.id}`)}
    >
      <Box sx={movieCardStyles.mediaContainer}>
        <CardMedia
          component="img"
          image={posterUrl}
          alt={movie.title}
          sx={movieCardStyles.cardMedia}
          onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
            if (!imageError) {
              setImageError(true);
              e.currentTarget.src = '';
            }
          }}
        />

        {watched && (
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontWeight: 700,
              fontSize: '1.1rem',
              letterSpacing: 1,
              zIndex: 2,
            }}
          >
            Watched
          </Box>
        )}
      </Box>

      <CardContent sx={{ p: 2 }}>
        <Typography variant="h6" noWrap sx={{ color: 'white', fontSize: '1.1rem' }}>
          {movie.title}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
          <Typography variant="body2" sx={{ color: '#888' }}>
            {year}
          </Typography>
          <Rating
            value={movie.vote_average ? movie.vote_average / 2 : 0}
            precision={0.1}
            readOnly
            size="small"
            sx={movieCardStyles.rating}
          />
          <Typography variant="body2" sx={{ color: '#888' }}>
            {movie.vote_average ? movie.vote_average.toFixed(1) : 'N/A'}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};
