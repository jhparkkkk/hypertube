import * as React from 'react';
import { useEffect, useRef, useState, useCallback } from 'react';
import { Box, CircularProgress, Typography, Button, IconButton, Slider } from '@mui/material';
import { PlayArrow, Pause, VolumeUp, VolumeOff, Fullscreen, Forward10, Replay10, Subtitles } from '@mui/icons-material';
import { api, API_BASE_URL } from '../../api/axiosConfig';
import { moviePlayerStyles } from './shared/styles';
import { useAuth } from '../../context/AuthContext';

interface MovieStatus {
  ready: boolean;
  downloading: boolean;
  file_path: string;
  status?: string;
  progress?: number;
  total_duration?: number;
  segment_duration?: number;
  available_segments?: number;
}

interface SegmentInfo {
  segment: number;
  filename: string;
  size: number;
}

interface SegmentsData {
  available_segments: SegmentInfo[];
  segment_duration: number;
  total_segments: number;
  total_duration?: number;
}

interface SubtitleCue {
  startTime: number;
  endTime: number;
  text: string;
}

interface SubtitleTrack {
  language: string;
  language_name: string;
  file_path: string;
}

interface MoviePlayerComponentProps {
  movieId: number;
  magnet: string;
}

const BUFFER_SEGMENTS = 2; // Number of segments to pre-buffer

const MoviePlayer: React.FC<MoviePlayerComponentProps> = ({ movieId, magnet }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [, setFilePath] = useState<string | null>(null);
  const [, setStatusData] = useState<MovieStatus | null>(null);
  const [retryCount] = useState(0);
  
  // Video elements and buffering
  const currentVideoRef = useRef<HTMLVideoElement>(null);
  const bufferVideoRefs = useRef<HTMLVideoElement[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(1);
  
  // Segment and time management
  const [currentSegment, setCurrentSegment] = useState(0);
  const [segmentsData, setSegmentsData] = useState<SegmentsData | null>(null);
  const [virtualTime, setVirtualTime] = useState(0);
  const [totalDuration, setTotalDuration] = useState(0);
  const [isBuffering, setIsBuffering] = useState(false);
  const [bufferedSegments, setBufferedSegments] = useState<number[]>([]);
  const [isTransitioning, setIsTransitioning] = useState(false);
  
  // Progress tracking
  const intervalRef = useRef<number | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const controlsTimeoutRef = useRef<number | null>(null);
  
  // Add new state for available time
  const [availableTime, setAvailableTime] = useState(0);

  const [subtitles, setSubtitles] = useState<SubtitleTrack[]>([]);
  const [currentSubtitle, setCurrentSubtitle] = useState<SubtitleTrack | null>(null);
  const [subtitlesEnabled, setSubtitlesEnabled] = useState(false);
  
  // Custom subtitle rendering
  const [subtitleCues, setSubtitleCues] = useState<SubtitleCue[]>([]);
  const [currentSubtitleText, setCurrentSubtitleText] = useState<string>('');

  const { user, loadingUser} = useAuth();

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  // Parse VTT time string to seconds
  const parseVTTTime = (timeString: string): number => {
    const parts = timeString.split(':');
    const hours = parseInt(parts[0]);
    const minutes = parseInt(parts[1]);
    const secondsParts = parts[2].split('.');
    const seconds = parseInt(secondsParts[0]);
    const milliseconds = parseInt(secondsParts[1] || '0');
    
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000;
  };

  // Parse VTT content into subtitle cues
  const parseVTTContent = (vttContent: string): SubtitleCue[] => {
    const lines = vttContent.split('\n');
    const cues: SubtitleCue[] = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      // Look for time range lines (e.g., "00:02:48.336 --> 00:02:50.171")
      if (line.includes(' --> ')) {
        const [startTimeStr, endTimeStr] = line.split(' --> ');
        const startTime = parseVTTTime(startTimeStr.trim());
        const endTime = parseVTTTime(endTimeStr.trim());
        
        // Collect subtitle text (next lines until empty line)
        const textLines: string[] = [];
        i++; // Move to next line after timestamp
        
        while (i < lines.length && lines[i].trim() !== '') {
          textLines.push(lines[i].trim());
          i++;
        }
        
        if (textLines.length > 0) {
          cues.push({
            startTime,
            endTime,
            text: textLines.join('\n')
          });
        }
      }
    }
    
    return cues;
  };

  // Update current subtitle text based on virtual time
  useEffect(() => {
    if (subtitleCues.length === 0) {
      setCurrentSubtitleText('');
      return;
    }

    const currentCue = subtitleCues.find(cue => 
      virtualTime >= cue.startTime && virtualTime <= cue.endTime
    );

    setCurrentSubtitleText(currentCue ? currentCue.text : '');
  }, [virtualTime, subtitleCues]);

  // Load and parse VTT file when subtitle is selected
  useEffect(() => {
    if (!currentSubtitle) {
      setSubtitleCues([]);
      setCurrentSubtitleText('');
      return;
    }

    const loadSubtitleFile = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/subtitles/${movieId}/file/${currentSubtitle.language}/`);
        if (response.ok) {
          const vttContent = await response.text();
          const cues = parseVTTContent(vttContent);
          setSubtitleCues(cues);
        }
      } catch (error) {
        console.error('Error loading subtitle file:', error);
        setSubtitleCues([]);
      }
    };

    loadSubtitleFile();
  }, [currentSubtitle, movieId]);

  // Initialize buffer video elements
  useEffect(() => {
    bufferVideoRefs.current = Array(BUFFER_SEGMENTS).fill(null).map(() => {
      const video = document.createElement('video');
      video.style.display = 'none';
      return video;
    });
    
    return () => {
      bufferVideoRefs.current.forEach(video => video.remove());
    };
  }, []);

  const checkStatus = useCallback(async () => {
    try {
      const response = await api.get<MovieStatus>(`/video/${movieId}/status/`);
      setStatusData(response.data);
      
      if (response.data.total_duration) {
        setTotalDuration(response.data.total_duration);
      }
      
      if (response.data.status === 'READY' || response.data.status === 'PLAYABLE' || response.data.ready) {
        setFilePath(response.data.file_path);
        setLoading(false);
        fetchSegmentInfo();
      } else if (!response.data.downloading && !response.data.ready) {
        await api.post(`/video/${movieId}/start/`, { magnet_link: magnet });
      }
    } catch (err) {
      setError(`Failed to check movie status: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setLoading(false);
    }
  }, [movieId, magnet]);

  const fetchSegmentInfo = useCallback(async () => {
    try {
      const response = await api.get<SegmentsData>(`/video/${movieId}/segments/`);
      setSegmentsData(response.data);
      if (response.data.total_duration) {
        setTotalDuration(response.data.total_duration);
      }
      // Calculate available time based on available segments
      const lastAvailableSegment = Math.max(...response.data.available_segments.map(seg => seg.segment));
      setAvailableTime((lastAvailableSegment + 1) * response.data.segment_duration);
    } catch (err) {
      console.error('Failed to fetch segment info:', err);
    }
  }, [movieId]);

  const preloadSegments = useCallback((baseSegment: number) => {
    if (!segmentsData) return;
    
    const segmentsToBuffer = Array.from({ length: BUFFER_SEGMENTS }, (_, i) => baseSegment + i + 1)
      .filter(seg => seg < segmentsData.total_segments && !bufferedSegments.includes(seg));
    
    segmentsToBuffer.forEach((segment, index) => {
      const video = bufferVideoRefs.current[index];
      if (!video) return;
      
      const src = `${API_BASE_URL}/video/${movieId}/stream/?segment=${segment}&t=${retryCount}`;
      video.src = src;
      video.load();
      
      video.oncanplaythrough = () => {
        setBufferedSegments(prev => [...prev, segment]);
      };
    });
  }, [movieId, retryCount, segmentsData, bufferedSegments]);

  const switchToSegment = useCallback((targetSegment: number, seekTime?: number) => {
    if (!currentVideoRef.current || !segmentsData || isTransitioning) return;
    
        setIsTransitioning(true);
    setIsBuffering(true);
        
        const newSrc = `${API_BASE_URL}/video/${movieId}/stream/?segment=${targetSegment}&t=${retryCount}`;
          const wasPlaying = !currentVideoRef.current.paused;
          
          currentVideoRef.current.style.opacity = '0.8';
          currentVideoRef.current.src = newSrc;
          
          const handleLoadedData = () => {
            if (currentVideoRef.current) {
        if (seekTime !== undefined) {
          currentVideoRef.current.currentTime = seekTime;
        }
              currentVideoRef.current.style.opacity = '1';
              setIsTransitioning(false);
        setIsBuffering(false);
              
              if (wasPlaying) {
                currentVideoRef.current.play().catch(console.error);
              }
        
        // Pre-load next segments
        preloadSegments(targetSegment);
            }
          };
          
          currentVideoRef.current.addEventListener('loadeddata', handleLoadedData, { once: true });
    setCurrentSegment(targetSegment);
  }, [movieId, retryCount, segmentsData, isTransitioning, preloadSegments]);

  // Add function to check if time is available
  const isTimeAvailable = useCallback((time: number) => {
    return time <= availableTime;
  }, [availableTime]);

  // Update handleSeek to check availability
  const handleSeek = useCallback((newTime: number) => {
    if (!segmentsData || !isTimeAvailable(newTime)) return;
    
    const targetSegment = Math.floor(newTime / segmentsData.segment_duration);
    const segmentTime = newTime % segmentsData.segment_duration;
    
    setVirtualTime(newTime);
    
    if (targetSegment !== currentSegment) {
      switchToSegment(targetSegment, segmentTime);
    } else if (currentVideoRef.current) {
        currentVideoRef.current.currentTime = segmentTime;
    }
  }, [segmentsData, currentSegment, switchToSegment, isTimeAvailable]);

  const skipForward = () => {
    handleSeek(Math.min(virtualTime + 10, totalDuration));
  };

  const skipBackward = () => {
    handleSeek(Math.max(virtualTime - 10, 0));
  };

  const togglePlayPause = () => {
    if (!currentVideoRef.current) return;
    
    if (isPlaying) {
      currentVideoRef.current.pause();
    } else {
      currentVideoRef.current.play();
    }
  };

  const handleVolumeChange = (_event: Event, newValue: number | number[]) => {
    const volumeValue = newValue as number;
    setVolume(volumeValue);
    if (currentVideoRef.current) {
      currentVideoRef.current.volume = volumeValue;
    }
    setIsMuted(volumeValue === 0);
  };

  const toggleMute = () => {
    if (!currentVideoRef.current) return;
    
    if (isMuted) {
      currentVideoRef.current.volume = volume;
      setIsMuted(false);
    } else {
      currentVideoRef.current.volume = 0;
      setIsMuted(true);
    }
  };

  const enterFullscreen = () => {
    if (currentVideoRef.current) {
      if (currentVideoRef.current.requestFullscreen) {
        currentVideoRef.current.requestFullscreen();
      }
    }
  };

  useEffect(() => {
    const interval = setInterval(() => {
      checkStatus();
      if (segmentsData) {
        fetchSegmentInfo();
      }
    }, 10000);
    
    checkStatus();
    return () => clearInterval(interval);
  }, [checkStatus, fetchSegmentInfo, segmentsData]);

  useEffect(() => {
    const updateTime = () => {
      if (!currentVideoRef.current || !segmentsData || isDragging || isTransitioning) return;
      
      const segmentTime = currentVideoRef.current.currentTime;
      const baseTime = currentSegment * segmentsData.segment_duration;
      const newVirtualTime = baseTime + segmentTime;
      
      setVirtualTime(newVirtualTime);
      
      // Check if we need to switch to next segment
      if (segmentTime >= segmentsData.segment_duration - 0.5) {
        const nextSegment = currentSegment + 1;
        if (nextSegment < segmentsData.total_segments && bufferedSegments.includes(nextSegment)) {
          switchToSegment(nextSegment);
        }
      }
    };

    if (isPlaying) {
      intervalRef.current = window.setInterval(updateTime, 100);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isPlaying, currentSegment, segmentsData, isDragging, isTransitioning, bufferedSegments, switchToSegment]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.code) {
        case 'Space':
          e.preventDefault();
          togglePlayPause();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          skipBackward();
          break;
        case 'ArrowRight':
          e.preventDefault();
          skipForward();
          break;
        case 'KeyM':
          e.preventDefault();
          toggleMute();
          break;
        case 'KeyF':
          e.preventDefault();
          enterFullscreen();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [virtualTime]);

  useEffect(() => {
    const hideControlsTimeout = () => {
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current);
      }
      controlsTimeoutRef.current = window.setTimeout(() => {
        if (isPlaying && !isDragging) {
          setShowControls(false);
        }
      }, 3000);
    };

    hideControlsTimeout();

    return () => {
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current);
      }
    };
  }, [isPlaying, isDragging]);

  const handleMouseMove = () => {
    setShowControls(true);
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current);
    }
    controlsTimeoutRef.current = window.setTimeout(() => {
      if (isPlaying && !isDragging) {
        setShowControls(false);
      }
    }, 3000);
  };

  // Fetch subtitles when component mounts
  useEffect(() => {
    const fetchSubtitles = async () => {
      try {
        const response = await api.get(`/subtitles/?movie_id=${movieId}&language=${user?.preferred_language || 'en'}`);
        setSubtitles(response.data);
      } catch (error) {
        console.error('Error fetching subtitles:', error);
      }
    };
    if (!loadingUser) {
          fetchSubtitles();
      }
  }, [movieId, user?.preferred_language, loadingUser]);

  // Handle subtitle toggle - automatically select first subtitle when enabled
  useEffect(() => {
      if (subtitlesEnabled) {
      // Select first available subtitle (usually English)
      if (subtitles.length > 0) {
        setCurrentSubtitle(subtitles[0]);
      }
    } else {
      // Disable subtitles
      setCurrentSubtitle(null);
    }
  }, [subtitlesEnabled, subtitles]);
  if (loading) {
    return (
      <Box sx={moviePlayerStyles.loadingContainer}>
				<CircularProgress size={60} thickness={3} sx={{ color: '#ff0000' }} />
				
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={moviePlayerStyles.errorContainer}>
          <Typography color="error">{error}</Typography>
        <Button variant="contained" color="primary" onClick={() => {
          setError(null);
          setLoading(true);
          checkStatus();
        }}>
            Retry
          </Button>
      </Box>
    );
  }

  return (
    <Box 
      sx={moviePlayerStyles.videoContainer}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setShowControls(true)}
    >
      <Box sx={{ position: 'relative', width: '100%', height: 0, paddingBottom: '56.25%', backgroundColor: '#000' }}>
        <video
          ref={currentVideoRef}
          style={{ 
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%', 
            height: '100%',
            objectFit: 'contain'
          }}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onWaiting={() => setIsBuffering(true)}
          onCanPlay={() => setIsBuffering(false)}
          onError={(e) => {
            console.error('Video error:', e);
            setError('Failed to load video segment');
          }}
          playsInline
          preload="auto"
          crossOrigin="anonymous"
        />
        
        {/* Custom subtitle overlay */}
        {currentSubtitleText && (
          <Box
            sx={{
              position: 'absolute',
              bottom: '10%',
              left: '50%',
              transform: 'translateX(-50%)',
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              color: 'white',
              padding: '8px 16px',
              borderRadius: '4px',
              fontSize: '18px',
              fontWeight: 500,
              textAlign: 'center',
              maxWidth: '80%',
              lineHeight: 1.4,
              whiteSpace: 'pre-line',
              textShadow: '2px 2px 4px rgba(0, 0, 0, 0.8)',
              zIndex: 10,
            }}
          >
            {currentSubtitleText}
          </Box>
        )}
        
        {/* Buffering indicator */}
        {isBuffering && (
          <Box sx={moviePlayerStyles.bufferingOverlay}>
            <CircularProgress size={40} sx={{ color: 'white' }} />
          </Box>
        )}
        
        {/* Controls overlay */}
        <Box
          sx={{
            ...moviePlayerStyles.controlsOverlay,
            opacity: showControls ? 1 : 0,
            transition: 'opacity 0.3s ease'
          }}
        >
          <Box sx={moviePlayerStyles.progressBarContainer}>
            <Box sx={{ 
              position: 'relative', 
              height: 4, 
              backgroundColor: '#333',
              display: 'flex',
              alignItems: 'center' 
            }}>
              {/* Available portion */}
              <Box
                sx={{
                  position: 'absolute',
                  left: 0,
                  top: 0,
                  height: '100%',
                  width: `${(availableTime / totalDuration) * 100}%`,
                  backgroundColor: '#666',
                  pointerEvents: 'none',
                }}
              />
              {/* Played portion */}
              <Box
                sx={{
                  position: 'absolute',
                  left: 0,
                  top: 0,
                  height: '100%',
                  width: `${(virtualTime / totalDuration) * 100}%`,
                  backgroundColor: '#ff0000',
                  pointerEvents: 'none',
                }}
              />
              <Slider
                value={virtualTime}
                min={0}
                max={totalDuration}
                onChange={(_, value) => {
                  const newTime = value as number;
                  if (isTimeAvailable(newTime)) {
                    setVirtualTime(newTime);
                    setIsDragging(true);
                  }
                }}
                onChangeCommitted={(_, value) => {
                  const newTime = value as number;
                  if (isTimeAvailable(newTime)) {
                    handleSeek(newTime);
                  }
                  setIsDragging(false);
                }}
                sx={{
                  ...moviePlayerStyles.progressSlider,
                  position: 'absolute',
                  padding: 0,
                  width: '100%',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  '& .MuiSlider-rail': {
                    opacity: 0,
                    backgroundColor: 'transparent',
                  },
                  '& .MuiSlider-track': {
                    opacity: 0,
                    backgroundColor: 'transparent',
                  },
                  '& .MuiSlider-thumb': {
                    display: isDragging ? 'block' : 'none',
                    '&:hover': {
                      display: 'block',
                    },
                  },
                  '&:hover .MuiSlider-thumb': {
                    display: 'block',
                  },
                }}
              />
            </Box>
          </Box>
          
          {/* Control buttons */}
          <Box sx={moviePlayerStyles.controlsContainer}>
            <Box sx={moviePlayerStyles.leftControls}>
              <IconButton onClick={togglePlayPause} sx={moviePlayerStyles.controlButton}>
                {isPlaying ? <Pause /> : <PlayArrow />}
              </IconButton>
              <IconButton onClick={skipBackward} sx={moviePlayerStyles.controlButton}>
                <Replay10 />
              </IconButton>
              <IconButton onClick={skipForward} sx={moviePlayerStyles.controlButton}>
                <Forward10 />
              </IconButton>
              <Box sx={moviePlayerStyles.volumeControl}>
                <IconButton onClick={toggleMute} sx={moviePlayerStyles.controlButton}>
                  {isMuted ? <VolumeOff /> : <VolumeUp />}
                </IconButton>
                <Slider
                  value={isMuted ? 0 : volume}
                  onChange={handleVolumeChange}
                  min={0}
                  max={1}
                  step={0.1}
                  sx={moviePlayerStyles.volumeSlider}
                />
              </Box>
              <IconButton 
                onClick={() => setSubtitlesEnabled(!subtitlesEnabled)}
                sx={{
                  ...moviePlayerStyles.controlButton,
                  color: subtitlesEnabled ? 'white' : 'rgba(255, 255, 255, 0.4)',
                  '&:hover': {
                    color: subtitlesEnabled ? 'white' : 'rgba(255, 255, 255, 0.7)',
                  }
                }}
              >
                <Subtitles />
              </IconButton>
              <Typography variant="body2" sx={moviePlayerStyles.timeDisplay}>
                {formatTime(virtualTime)} / {formatTime(totalDuration)}
              </Typography>
            </Box>
            
            <Box sx={moviePlayerStyles.rightControls}>
              <IconButton onClick={enterFullscreen} sx={moviePlayerStyles.controlButton}>
                <Fullscreen />
              </IconButton>
            </Box>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default MoviePlayer; 