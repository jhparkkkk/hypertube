import React, { useEffect, useRef, useState } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { api } from '../../api/axiosConfig';

interface MoviePlayerProps {
  movieId: string;
  onError?: (error: string) => void;
}

export const MoviePlayer: React.FC<MoviePlayerProps> = ({ movieId, onError }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filePath, setFilePath] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await api.get(`/streaming/${movieId}/status/`);
        if (response.data.status === 'READY') {
          const streamResponse = await api.get(`/streaming/${movieId}/stream/`);
          if (streamResponse.data.file_path) {
            setFilePath(streamResponse.data.file_path);
            setLoading(false);
          }
        }
      } catch (err) {
        const errorMessage = 'Failed to check movie status';
        setError(errorMessage);
        onError?.(errorMessage);
        setLoading(false);
      }
    };

    const interval = setInterval(checkStatus, 5000);
    checkStatus();

    return () => clearInterval(interval);
  }, [movieId, onError]);

  const handleError = (e: React.SyntheticEvent<HTMLVideoElement, Event>) => {
    const errorMessage = 'Failed to load video';
    setError(errorMessage);
    onError?.(errorMessage);
    setLoading(false);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  if (!filePath) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <Typography>Loading video...</Typography>
      </Box>
    );
  }

  return (
    <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
      <video
        ref={videoRef}
        controls
        style={{ maxWidth: '100%', maxHeight: '100%' }}
        onError={handleError}
      >
        <source src={`/streaming/${movieId}/play/`} type="video/mp4" />
        Your browser does not support the video tag.
      </video>
    </Box>
  );
}; 