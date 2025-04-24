import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, CircularProgress, LinearProgress } from '@mui/material';
import { api } from '../../api/axiosConfig';
import { moviePlayerStyles } from './shared/styles';

interface MoviePlayerProps {
  movieId: string;
  onError?: (error: string) => void;
}

export const MoviePlayer: React.FC<MoviePlayerProps> = ({ movieId, onError }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadStatus, setDownloadStatus] = useState<string>('PENDING');
  const [downloadProgress, setDownloadProgress] = useState<number>(0);
  const videoRef = useRef<HTMLVideoElement>(null);
  const statusInterval = useRef<NodeJS.Timeout>();

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await api.get(`/streaming/${movieId}/status/`);
        const { status, progress } = response.data;
        setDownloadStatus(status);
        setDownloadProgress(progress);

        if (status === 'READY' || status === 'ERROR') {
          if (statusInterval.current) {
            clearInterval(statusInterval.current);
          }
          setLoading(false);
        }
      } catch (err) {
        const errorMessage = 'Failed to check movie status';
        setError(errorMessage);
        onError?.(errorMessage);
        setLoading(false);
      }
    };

    const startStreaming = async () => {
      try {
        if (videoRef.current) {
          videoRef.current.src = `/streaming/${movieId}/stream/`;
          videoRef.current.load();
        }
      } catch (err) {
        const errorMessage = 'Failed to start streaming';
        setError(errorMessage);
        onError?.(errorMessage);
      }
    };

    // Start checking status immediately
    checkStatus();

    // Set up interval for status checks
    statusInterval.current = setInterval(checkStatus, 1000);

    // Start streaming if status is appropriate
    if (downloadStatus === 'DOWNLOADING' || downloadStatus === 'CONVERTING' || downloadStatus === 'READY') {
      startStreaming();
    }

    return () => {
      if (statusInterval.current) {
        clearInterval(statusInterval.current);
      }
    };
  }, [movieId, onError, downloadStatus]);

  const handleError = (e: React.SyntheticEvent<HTMLVideoElement, Event>) => {
    const errorMessage = 'Failed to load video';
    setError(errorMessage);
    onError?.(errorMessage);
    setLoading(false);
  };

  if (loading) {
    return (
      <Box sx={moviePlayerStyles.loadingContainer}>
        <CircularProgress />
        <Typography>Loading video...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={moviePlayerStyles.errorContainer}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  return (
    <Box sx={moviePlayerStyles.videoContainer}>
      <video
        ref={videoRef}
        controls
        style={{ width: '100%', height: '100%' }}
        onError={handleError}
      >
        <source src={`/streaming/${movieId}/stream/`} type="video/mp4" />
        Your browser does not support the video tag.
      </video>
      {(downloadStatus === 'DOWNLOADING' || downloadStatus === 'CONVERTING') && (
        <Box sx={moviePlayerStyles.downloadProgress}>
          <Typography variant="body2" color="white">
            {downloadStatus === 'DOWNLOADING' ? 'Downloading' : 'Converting'}...
          </Typography>
          <LinearProgress
            variant="determinate"
            value={downloadProgress}
            sx={{ width: '100%', mt: 1 }}
          />
        </Box>
      )}
    </Box>
  );
}; 