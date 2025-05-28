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
      const response = await api.get<MovieStatus>(`/video/${movieId}/status/`);
      setStatusData(response.data);
      
      if (response.data.status === 'READY' || response.data.status === 'PLAYABLE' || response.data.ready) {
        setFilePath(response.data.file_path);
        setLoading(false);
      } else if (!response.data.downloading && !response.data.ready) {
        await api.post(`/video/${movieId}/start/`, { magnet_link: magnet });
      }
    } catch (err) {
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
    const videoElement = e.target as HTMLVideoElement;
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
      videoRef.current.play().catch(console.error);
    }
  };

  const getStatusMessage = () => {
    if (!statusData) return 'Checking status...';
    
    const status = statusData.status || (statusData.downloading ? 'Downloading' : statusData.ready ? 'Ready' : 'Preparing');
    const progress = statusData.progress ? ` (${Math.round(statusData.progress)}%)` : '';
    
    if (status === 'PLAYABLE') {
      return `Loading first segment... Rest of the movie will continue downloading${progress}`;
    }
    
    return `Status: ${status}${progress}`;
  };

  if (loading) {
    return (
      <Box sx={moviePlayerStyles.loadingContainer}>
        <CircularProgress />
        <Typography>
          {getStatusMessage()}
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
      {statusData?.status === 'PLAYABLE' && (
        <Typography variant="body2" sx={{ mt: 1, textAlign: 'center', color: 'text.secondary' }}>
          First segment ready. Continuing to download the rest of the movie...
        </Typography>
      )}
    </Box>
  );
};

export default MoviePlayer; 