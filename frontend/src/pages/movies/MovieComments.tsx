import React, { useEffect, useState } from 'react';
import { Box, Typography, TextField, Button, Divider, Snackbar, Alert, IconButton } from '@mui/material';
import { Delete, Edit, Save, Cancel } from '@mui/icons-material';
import { api } from '../../api/axiosConfig';
import { useAuth } from '../../context/AuthContext';

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
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editedContent, setEditedContent] = useState('');
  const { user } = useAuth();

  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({ open: false, message: '', severity: 'success' });

  const showMessage = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  const fetchComments = async () => {
    try {
      const res = await api.get(`/movies/${movieId}/comments/`);
      setComments(res.data);
    } catch (err) {
      console.error('Error fetching comments:', err);
      showMessage('Failed to load comments', 'error');
    }
  };

  const postComment = async () => {
		if (!newComment.trim()) return;
		
		const trimmed = newComment.trim();
		if (trimmed.length > 500) {
			showMessage("Comment is too long (500 characters max)", "error");
    	return;
  	}
    try {
      await api.post(`/comments/`, { movie_id: movieId, content: newComment });
      setNewComment('');
      fetchComments();
      showMessage('Comment posted successfully', 'success');
    } catch (err) {
      console.error('Error posting comment:', err);
      setError('Failed to post comment');
      showMessage('Failed to post comment', 'error');
    }
  };

  const deleteComment = async (id: number) => {
    try {
      await api.delete(`/comments/${id}/`);
      fetchComments();
      showMessage('Comment deleted', 'success');
    } catch (err) {
      console.error('Error deleting comment:', err);
      showMessage('Failed to delete comment', 'error');
    }
  };

  const saveEditedComment = async (id: number) => {
    try {
      await api.patch(`/comments/${id}/`, { content: editedContent });
      setEditingId(null);
      setEditedContent('');
      fetchComments();
      showMessage('Comment updated', 'success');
    } catch (err) {
      console.error('Error updating comment:', err);
      showMessage('Failed to update comment', 'error');
    }
  };

  useEffect(() => {
    fetchComments();
  }, [movieId]);

  return (
    <Box sx={{ mt: 4,
			backgroundColor: '#2a2a2a',
			p: 3,
			borderRadius: 2,
			maxWidth: '100%',
    	overflowWrap: 'break-word',
    	wordBreak: 'break-word',
		 }}>
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
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="subtitle2" color="white">
              {comment.username || 'Anonymous'} — {new Date(comment.created_at).toLocaleString()}
            </Typography>
            {user?.username === comment.username && editingId !== comment.id && (
              <Box>
                <IconButton size="small" onClick={() => { setEditingId(comment.id); setEditedContent(comment.content); }}>
                  <Edit sx={{ color: 'white', fontSize: 18 }} />
                </IconButton>
                <IconButton size="small" onClick={() => deleteComment(comment.id)}>
                  <Delete sx={{ color: 'white', fontSize: 18 }} />
                </IconButton>
              </Box>
            )}
          </Box>

          {editingId === comment.id ? (
            <Box>
              <TextField
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                fullWidth
                multiline
                sx={{ mt: 1, mb: 1, backgroundColor: '#1a1a1a', input: { color: 'white' } }}
              />
              <Button
                variant="contained"
                color="success"
                size="small"
                onClick={() => saveEditedComment(comment.id)}
                sx={{ mr: 1 }}
              >
                Save
              </Button>
              <Button
                variant="outlined"
                size="small"
                onClick={() => setEditingId(null)}
              >
                Cancel
              </Button>
            </Box>
          ) : (
            <Typography variant="body2" color="#ccc">
              {comment.content}
            </Typography>
          )}

          <Divider sx={{ my: 1, borderColor: '#333' }} />
        </Box>
      ))}

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          severity={snackbar.severity}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default MovieComments;
