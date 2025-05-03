import React, { useEffect, useState } from 'react';
import { Box, Typography, TextField, Button, Divider } from '@mui/material';
import { api } from '../../api/axiosConfig';

interface Comment {
  id: number;
  content: string;
  created_at: string;
  username: string;
}

interface Props {
  movieId: number;
}

const MovieComments: React.FC<Props> = ({ movieId }) => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [error, setError] = useState('');

  const fetchComments = async () => {
    try {
      const res = await api.get(`/movies/${movieId}/comments/`);
			console.log('Fetched comments:', res.data);
      setComments(res.data);
    } catch (err) {
      console.error('Error fetching comments:', err);
    }
  };

  const postComment = async () => {
    if (!newComment.trim()) return;

    try {
			console.log('Posting comment:', newComment);
			console.log('Movie ID:', movieId);
      await api.post(`/comments/`, { movie_id: movieId, content: newComment });
      setNewComment('');
      fetchComments();
    } catch (err) {
      console.error('Error posting comment:', err);
      setError('Failed to post comment');
    }
  };

  useEffect(() => {
    fetchComments();
  }, [movieId]);

  return (
    <Box sx={{ mt: 4, backgroundColor: '#2a2a2a', p: 3, borderRadius: 2 }}>
      <Typography variant="h6" color="white" gutterBottom>
        Comments
      </Typography>

      <TextField
        multiline
        rows={3}
        value={newComment}
        onChange={(e) => setNewComment(e.target.value)}
        placeholder="Leave a comment..."
        fullWidth
        sx={{ mb: 2, backgroundColor: '#1a1a1a', input: { color: 'white' } }}
      />

      {error && (
        <Typography color="error" variant="body2" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      <Button
        variant="contained"
        color="primary"
        onClick={postComment}
        disabled={!newComment.trim()}
        sx={{ mb: 3 }}
      >
        Post Comment
      </Button>

      <Divider sx={{ borderColor: '#444', mb: 2 }} />

      {comments.map((comment) => (
        <Box key={comment.id} sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="white">
            {comment.username || 'Anonymous'} — {new Date(comment.created_at).toLocaleString()}
          </Typography>
          <Typography variant="body2" color="#ccc">
            {comment.content}
          </Typography>
          <Divider sx={{ my: 1, borderColor: '#333' }} />
        </Box>
      ))}
    </Box>
  );
};

export default MovieComments;
