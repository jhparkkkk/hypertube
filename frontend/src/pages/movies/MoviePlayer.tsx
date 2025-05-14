import React, { useEffect, useRef, useState } from 'react';
import { Box, CircularProgress, Typography, Button } from '@mui/material';
import { api, API_BASE_URL } from '../../api/axiosConfig';
import { MoviePlayerProps } from './shared/types';
import { moviePlayerStyles } from './shared/styles';

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
  const [retryCount, setRetryCount] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const checkStatus = async () => {
    try {
    //   console.log('Checking movie status...');
      const response = await api.get<MovieStatus>(`/video/${movieId}/status/`);
    //   console.log('Status response:', response.data);
      setStatusData(response.data);
      
      if (response.data.status === 'READY' || response.data.ready) {
        // console.log('Movie is ready, setting file path:', response.data.file_path);
        setFilePath(response.data.file_path);
        setLoading(false);
      } else if (!response.data.downloading && !response.data.ready) {
        // console.log('Starting download...');
        await api.post(`/video/${movieId}/start/`, { magnet_link: magnet });
      }
    } catch (err) {
      // console.error('Error checking movie status:', err);
      setError(`Failed to check movie status: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setLoading(false);
    }
  };

  useEffect(() => {
    const interval = setInterval(checkStatus, 5000);
    checkStatus();
    return () => clearInterval(interval);
  }, [movieId, magnet]);

  const handleError = (e: React.SyntheticEvent<HTMLVideoElement, Event>) => {
    // console.error('Video player error:', e);
    const videoElement = e.target as HTMLVideoElement;
    // console.error('Video error details:', {
    //   error: videoElement.error?.message || videoElement.error,
    //   networkState: videoElement.networkState,
    //   readyState: videoElement.readyState,
    //   currentSrc: videoElement.currentSrc,
    //   currentTime: videoElement.currentTime
    // });
    setError('Failed to load video. Please try refreshing the page.');
    setLoading(false);
  };

  const handleRetry = async () => {
    setError(null);
    setLoading(true);
    setRetryCount(prev => prev + 1);
    await checkStatus();
  };

  const handlePlay = () => {
    setIsPlaying(true);
  };

  const handlePause = () => {
    setIsPlaying(false);
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current && !isPlaying) {
      // Start playing when metadata is loaded
      videoRef.current.play().catch(console.error);
    }
  };

  if (loading) {
    return (
      <Box sx={moviePlayerStyles.loadingContainer}>
        <CircularProgress />
        <Typography>
          {statusData ? 
            `Status: ${statusData.status || (statusData.downloading ? 'Downloading' : statusData.ready ? 'Ready' : 'Preparing')} ${statusData.progress ? `(${Math.round(statusData.progress)}%)` : ''}`
            : 'Checking status...'}
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={moviePlayerStyles.errorContainer}>
        <Box display="flex" flexDirection="column" alignItems="center" gap={2}>
          <Typography color="error">{error}</Typography>
          <Button variant="contained" color="primary" onClick={handleRetry}>
            Retry
          </Button>
          <Typography variant="body2" color="textSecondary">
            File path: {filePath || 'Not available'}
          </Typography>
        </Box>
      </Box>
    );
  }

  return (
    <Box sx={moviePlayerStyles.videoContainer}>
      <video
        ref={videoRef}
        controls
        style={{ width: '100%', height: 'auto' }}
        onError={handleError}
        onPlay={handlePlay}
        onPause={handlePause}
        onLoadedMetadata={handleLoadedMetadata}
        src={`${API_BASE_URL}/video/${movieId}/stream/?t=${retryCount}`}
        crossOrigin="anonymous"
        playsInline
        preload="metadata"
      >
        Your browser does not support the video tag.
      </video>
    </Box>
  );
};

export default MoviePlayer; 