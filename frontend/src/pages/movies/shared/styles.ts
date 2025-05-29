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
    gap: 2,
    backgroundColor: '#000',
  },
  errorContainer: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    height: '400px',
    gap: 2,
  },
  videoContainer: {
    position: 'relative',
    width: '100%',
    backgroundColor: '#000',
    overflow: 'hidden',
  },
  bufferingOverlay: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    color: 'white',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 1,
  },
  controlsOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    background: 'linear-gradient(transparent, rgba(0,0,0,0.7))',
    padding: 2,
    color: 'white',
  },
  progressBarContainer: {
    marginBottom: 2,
    padding: '0 2px',
    '&:hover': {
      '& .progress-thumb': {
        opacity: 1,
      },
    },
  },
  progressSlider: {
    color: '#ff0000',
    height: 4,
    padding: '15px 0',
    '& .MuiSlider-thumb': {
      width: 12,
      height: 12,
      transition: '0.2s cubic-bezier(.47,1.64,.41,.8)',
      opacity: 0,
      backgroundColor: '#fff',
      top: '50%',
      marginTop: -6,
      marginLeft: -6,
      '&:hover, &.Mui-focusVisible': {
        boxShadow: '0px 0px 0px 8px rgba(255, 255, 255, 0.16)',
        opacity: 1,
      },
      '&.Mui-active': {
        width: 16,
        height: 16,
        marginTop: -8,
        marginLeft: -8,
        opacity: 1,
      },
    },
    '& .MuiSlider-rail': {
      opacity: 1,
      backgroundColor: '#333',
    },
    '& .MuiSlider-track': {
      border: 'none',
      opacity: 0,
    },
  },
  controlsContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  leftControls: {
    display: 'flex',
    alignItems: 'center',
    gap: 1,
  },
  rightControls: {
    display: 'flex',
    alignItems: 'center',
    gap: 1,
  },
  controlButton: {
    color: 'white',
    '&:hover': {
      backgroundColor: 'rgba(255, 255, 255, 0.1)',
    },
  },
  volumeControl: {
    display: 'flex',
    alignItems: 'center',
    width: 140,
  },
  volumeSlider: {
    width: 80,
    color: 'white',
    '& .MuiSlider-track': {
      border: 'none',
    },
    '& .MuiSlider-thumb': {
      width: 12,
      height: 12,
      backgroundColor: '#fff',
      '&:hover, &.Mui-focusVisible': {
        boxShadow: '0px 0px 0px 8px rgba(255, 255, 255, 0.16)',
      },
    },
  },
  timeDisplay: {
    marginLeft: 2,
    minWidth: 100,
  },
} as const; 