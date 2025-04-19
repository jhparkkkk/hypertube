import React, { useEffect, useRef, useState } from 'react';
import { Box, CircularProgress, Typography, LinearProgress } from '@mui/material';
import { api } from '../../api/axiosConfig';
import { MoviePlayerProps, DownloadStatus } from './shared/types';
import { moviePlayerStyles } from './shared/styles';

const MoviePlayer: React.FC<MoviePlayerProps> = ({ movieId }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [downloadStatus, setDownloadStatus] = useState<DownloadStatus>('PENDING');

  useEffect(() => {
    const checkMovieStatus = async () => {
      try {
        const response = await api.get(`/movies/${movieId}/status`);
        const { download_status, download_progress } = response.data;
        
        setDownloadStatus(download_status);
        setDownloadProgress(download_progress || 0);

        if (download_status === 'READY') {
          setLoading(false);
        } else if (download_status === 'ERROR') {
          setError('Error processing movie');
        }
      } catch (err) {
        setError('Error fetching movie status');
      }
    };

    // Check status immediately and then every 5 seconds
    checkMovieStatus();
    const interval = setInterval(checkMovieStatus, 5000);

    return () => clearInterval(interval);
  }, [movieId]);

  const getStatusMessage = () => {
    switch (downloadStatus) {
      case 'PENDING':
        return 'Preparing to download...';
      case 'DOWNLOADING':
        return `Downloading movie... ${Math.round(downloadProgress)}%`;
      case 'CONVERTING':
        return 'Converting video format...';
      case 'ERROR':
        return 'Error processing movie';
      default:
        return 'Loading...';
    }
  };

  if (loading) {
    return (
      <Box sx={moviePlayerStyles.loadingContainer}>
        <CircularProgress />
        <Typography variant="body1" color="textSecondary">
          {getStatusMessage()}
        </Typography>
        {downloadStatus === 'DOWNLOADING' && (
          <Box sx={moviePlayerStyles.progressBar}>
            <LinearProgress 
              variant="determinate" 
              value={downloadProgress} 
              sx={{ height: 8, borderRadius: 4 }}
            />
          </Box>
        )}
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={moviePlayerStyles.errorContainer}>
        <Typography variant="h6">{error}</Typography>
      </Box>
    );
  }

  return (
    <Box sx={moviePlayerStyles.videoContainer}>
      <video
        ref={videoRef}
        controls
        style={{ width: '100%', height: 'auto' }}
        src={`${api.defaults.baseURL}/movies/${movieId}/stream`}
      >
        <track
          kind="subtitles"
          src={`${api.defaults.baseURL}/movies/${movieId}/subtitles`}
          srcLang="en"
          label="English"
        />
        Your browser does not support the video tag.
      </video>
    </Box>
  );
};

export default MoviePlayer; 