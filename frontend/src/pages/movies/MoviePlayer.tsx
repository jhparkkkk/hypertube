import React, { useEffect, useRef, useState } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { api, API_BASE_URL } from '../../api/axiosConfig';
import { MoviePlayerProps } from './shared/types';

interface MovieStatus {
  ready: boolean;
  downloading: boolean;
  file_path: string;
  status?: string;
  progress?: number;
}

const MoviePlayer: React.FC<MoviePlayerProps> = ({ movieId, magnet }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filePath, setFilePath] = useState<string | null>(null);
  const [statusData, setStatusData] = useState<MovieStatus | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        console.log('Checking movie status...');
        const response = await api.get<MovieStatus>(`/video/${movieId}/status/`);
        console.log('Status response:', response.data);
        setStatusData(response.data);
        
        if (response.data.status === 'READY' || response.data.ready) {
          console.log('Movie is ready, setting file path:', response.data.file_path);
          setFilePath(response.data.file_path);
          setLoading(false);
        } else if (!response.data.downloading && !response.data.ready) {
          console.log('Starting download...');
          await api.post(`/video/${movieId}/start/`, { magnet_link: magnet });
        }
      } catch (err) {
        console.error('Error checking movie status:', err);
        setError(`Failed to check movie status: ${err instanceof Error ? err.message : 'Unknown error'}`);
        setLoading(false);
      }
    };

    const interval = setInterval(checkStatus, 5000);
    checkStatus();

    return () => clearInterval(interval);
  }, [movieId, magnet]);

  const handleError = (e: React.SyntheticEvent<HTMLVideoElement, Event>) => {
    console.error('Video player error:', e);
    const videoElement = e.target as HTMLVideoElement;
    console.error('Video error details:', {
      error: videoElement.error?.message || videoElement.error,
      networkState: videoElement.networkState,
      readyState: videoElement.readyState,
      currentSrc: videoElement.currentSrc
    });
    setError('Failed to load video. Please try refreshing the page.');
    setLoading(false);
  };

  if (loading) {
    return (
      <Box display="flex" flexDirection="column" justifyContent="center" alignItems="center" height="100vh" gap={2}>
        <CircularProgress />
        <Typography>
          {statusData ? 
            `Status: ${statusData.status || (statusData.downloading ? 'Downloading' : statusData.ready ? 'Ready' : 'Preparing')} ${statusData.progress ? `(${statusData.progress}%)` : ''}`
            : 'Checking status...'}
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box display="flex" flexDirection="column" justifyContent="center" alignItems="center" height="100vh" gap={2}>
        <Typography color="error">{error}</Typography>
        <Typography variant="body2" color="textSecondary">
          File path: {filePath || 'Not available'}
        </Typography>
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
        src={`${API_BASE_URL}/video/${movieId}/stream/`}
      />
    </Box>
  );
};

export default MoviePlayer; 