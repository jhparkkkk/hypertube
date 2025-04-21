import { SxProps } from '@mui/material';

export const movieCardStyles = {
  card: {
    height: '100%',
    position: 'relative',
    cursor: 'pointer',
    backgroundColor: '#2a2a2a',
    '&:hover': {
      transform: 'scale(1.02)',
      transition: 'transform 0.2s ease-in-out',
    },
  },
  cardMedia: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    backgroundColor: '#1a1a1a'
  },
  mediaContainer: {
    position: 'relative',
    paddingTop: '150%',
    backgroundColor: '#1a1a1a',
  },
  rating: {
    color: '#f5c518',
    '& .MuiRating-icon': {
      fontSize: '1rem'
    }
  }
} as const;

export const moviePlayerStyles = {
  loadingContainer: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    height: '400px',
    gap: 2
  },
  progressBar: {
    width: '80%',
    maxWidth: 400
  },
  errorContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '400px',
    color: 'error.main'
  },
  videoContainer: {
    width: '100%',
    maxWidth: '1000px',
    margin: '0 auto',
    bgcolor: '#000',
    position: 'relative'
  },
  bufferingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    zIndex: 1,
    gap: 2,
    color: 'white'
  },
  downloadProgress: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: '8px 16px',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center'
  }
} as const; 