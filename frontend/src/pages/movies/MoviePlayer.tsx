import React, { useEffect, useRef, useState } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { api } from '../../api/axiosConfig';
import { MoviePlayerProps } from './shared/types';

interface MovieStatus {
  ready: boolean;
  downloading: boolean;
  file_path: string;
}

export const MoviePlayer: React.FC<MoviePlayerProps> = ({ movieId, magnet }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filePath, setFilePath] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await api.get<MovieStatus>(`/streaming/${movieId}/status/`);
        if (response.data.ready) {
          setFilePath(response.data.file_path);
          setLoading(false);
        } else if (!response.data.downloading) {
          await api.post(`/streaming/${movieId}/start/`, { magnet_link: magnet });
        }
      } catch (err) {
        setError('Failed to check movie status');
        setLoading(false);
      }
    };

    const interval = setInterval(checkStatus, 5000);
    checkStatus();

    return () => clearInterval(interval);
  }, [movieId, magnet]);

  const handleError = (e: React.SyntheticEvent<HTMLVideoElement, Event>) => {
    setError('Failed to load video');
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
        <Typography>Downloading movie...</Typography>
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