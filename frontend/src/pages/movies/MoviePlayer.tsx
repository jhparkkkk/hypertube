import React, { useEffect, useRef, useState } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { DownloadStatus, MoviePlayerProps, MovieStatusResponse } from './shared/types';
import { api } from '../../api/axiosConfig';

const CHUNK_SIZE = 1024 * 1024; // 1MB chunks
const BUFFER_SIZE = 5 * CHUNK_SIZE; // 5MB buffer
const MIME_CODEC = 'video/mp4; codecs="avc1.42E01E,mp4a.40.2"';

const MoviePlayer: React.FC<MoviePlayerProps> = ({ movieId }: MoviePlayerProps) => {
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadProgress, setDownloadProgress] = useState<number>(0);
  const [canPlay, setCanPlay] = useState<boolean>(false);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaSourceRef = useRef<MediaSource | null>(null);
  const sourceBufferRef = useRef<SourceBuffer | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const currentByteRef = useRef<number>(0);
  const isStreamingRef = useRef<boolean>(false);
  const queuedChunksRef = useRef<ArrayBuffer[]>([]);
  const isAppendingRef = useRef<boolean>(false);

  useEffect(() => {
    checkMovieStatus();
    return () => {
      cleanup();
    };
  }, [movieId]);

  const cleanup = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (sourceBufferRef.current && mediaSourceRef.current) {
      try {
        if (sourceBufferRef.current.updating) {
          sourceBufferRef.current.abort();
        }
        if (mediaSourceRef.current.readyState === 'open') {
          mediaSourceRef.current.endOfStream();
        }
      } catch (err) {
        console.error('Error during cleanup:', err);
      }
    }
    isStreamingRef.current = false;
    queuedChunksRef.current = [];
    isAppendingRef.current = false;
  };

  const checkMovieStatus = async () => {
    try {
      const { data } = await api.get<MovieStatusResponse>(`/movies/${movieId}/status/`);

      if (data.error) {
        setError(data.error);
        return;
      }

      if (data.status === DownloadStatus.ERROR) {
        setError('An error occurred while processing the movie');
        return;
      }

      setDownloadProgress(data.progress || 0);

      if (data.status === DownloadStatus.READY || (data.status === DownloadStatus.DOWNLOADING && data.progress >= 5)) {
        if (!isStreamingRef.current) {
          initializeMediaSource();
        }
      } else {
        setTimeout(checkMovieStatus, 2000);
      }
    } catch (err: unknown) {
      let errorMessage = 'Failed to check movie status';
      if (err instanceof Error) {
        errorMessage = `Error: ${err.message}`;
      }
      setError(errorMessage);
      console.error('Movie status check failed:', err);
    }
  };

  const appendNextChunk = async () => {
    if (isAppendingRef.current || !sourceBufferRef.current || sourceBufferRef.current.updating) {
      return;
    }

    try {
      if (queuedChunksRef.current.length > 0) {
        isAppendingRef.current = true;
        const chunk = queuedChunksRef.current.shift();
        if (chunk) {
          sourceBufferRef.current.appendBuffer(chunk);
        }
      }
    } catch (err) {
      console.error('Error appending chunk:', err);
      if (err instanceof Error && err.name === 'QuotaExceededError') {
        // If buffer is full, remove some data from the start
        if (sourceBufferRef.current && sourceBufferRef.current.buffered.length > 0) {
          const start = sourceBufferRef.current.buffered.start(0);
          const end = sourceBufferRef.current.buffered.start(0) + 10;
          sourceBufferRef.current.remove(start, end);
        }
      }
    } finally {
      isAppendingRef.current = false;
    }
  };

  const initializeMediaSource = () => {
    if (!videoRef.current) return;

    try {
      if (!MediaSource.isTypeSupported(MIME_CODEC)) {
        throw new Error('Codec not supported');
      }

      const mediaSource = new MediaSource();
      mediaSourceRef.current = mediaSource;

      mediaSource.addEventListener('sourceopen', () => {
        try {
          if (mediaSource.readyState !== 'open') {
            console.error('MediaSource not open during sourceopen event');
            return;
          }

          const sourceBuffer = mediaSource.addSourceBuffer(MIME_CODEC);
          sourceBufferRef.current = sourceBuffer;
          
          sourceBuffer.addEventListener('updateend', () => {
            appendNextChunk();
            if (!sourceBuffer.updating) {
              fetchNextChunk();
            }
          });

          sourceBuffer.addEventListener('error', (e) => {
            console.error('SourceBuffer error:', e);
            setError('Error buffering video');
          });

          isStreamingRef.current = true;
          fetchNextChunk();
        } catch (err) {
          console.error('Error in sourceopen handler:', err);
          setError('Failed to initialize video player');
        }
      });

      mediaSource.addEventListener('sourceended', () => {
        console.log('MediaSource ended');
      });

      mediaSource.addEventListener('sourceclose', () => {
        console.log('MediaSource closed');
      });

      videoRef.current.src = URL.createObjectURL(mediaSource);
    } catch (err) {
      console.error('Error initializing MediaSource:', err);
      setError('Failed to initialize video player');
    }
  };

  const fetchNextChunk = async () => {
    if (!sourceBufferRef.current || !mediaSourceRef.current || sourceBufferRef.current.updating) {
      return;
    }

    try {
      abortControllerRef.current = new AbortController();
      
      const response = await api.get(`/movies/${movieId}/stream/`, {
        headers: {
          Range: `bytes=${currentByteRef.current}-${currentByteRef.current + CHUNK_SIZE - 1}`
        },
        responseType: 'arraybuffer',
        signal: abortControllerRef.current.signal
      });

      if (!response.data || response.data.byteLength === 0) {
        if (mediaSourceRef.current.readyState === 'open') {
          mediaSourceRef.current.endOfStream();
        }
        return;
      }

      currentByteRef.current += response.data.byteLength;
      queuedChunksRef.current.push(response.data);
      setIsLoading(false);

      if (!sourceBufferRef.current.updating) {
        appendNextChunk();
      }

    } catch (err: unknown) {
      if (err instanceof Error && err.name !== 'AbortError') {
        console.error('Error fetching chunk:', err);
        if (!isStreamingRef.current) {
          setError('Failed to stream video');
        }
      }
    }
  };

  if (error) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  return (
    <Box position="relative" width="100%" height="100%">
      <video
        ref={videoRef}
        controls
        style={{ width: '100%', maxHeight: '80vh', backgroundColor: '#000' }}
        onCanPlay={() => {
          setCanPlay(true);
          if (videoRef.current) {
            videoRef.current.play().catch(err => {
              console.error('Error auto-playing video:', err);
            });
          }
        }}
        onError={(e) => {
          const videoError = (e.target as HTMLVideoElement).error;
          console.error('Video error:', videoError?.message || e);
          setError('Error playing video');
        }}
        onTimeUpdate={() => {
          if (videoRef.current && !isAppendingRef.current) {
            const bufferedEnd = videoRef.current.buffered.length > 0 
              ? videoRef.current.buffered.end(videoRef.current.buffered.length - 1)
              : 0;
            const currentTime = videoRef.current.currentTime;
            
            if (bufferedEnd - currentTime < BUFFER_SIZE) {
              fetchNextChunk();
            }
          }
        }}
      />
      {(isLoading || !canPlay) && (
        <Box
          position="absolute"
          top={0}
          left={0}
          right={0}
          bottom={0}
          display="flex"
          flexDirection="column"
          justifyContent="center"
          alignItems="center"
          bgcolor="rgba(0, 0, 0, 0.7)"
        >
          <CircularProgress />
          {downloadProgress > 0 && (
            <Box mt={2}>
              <Typography color="white">
                Downloading: {Math.round(downloadProgress)}%
              </Typography>
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
};

export default MoviePlayer; 