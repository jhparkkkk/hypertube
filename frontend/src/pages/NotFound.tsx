import { Box, Typography, Button } from "@mui/material";
import { useNavigate } from "react-router-dom";

const NotFound = () => {
	const navigate = useNavigate();

	return (
		<Box
			display="flex"
			flexDirection="column"
			alignItems="center"
			justifyContent="center"
			height="100vh"
			textAlign="center"
			px={2}
		>
			<Typography variant="h2" fontWeight="bold" color="error" gutterBottom>
				404
			</Typography>
			<Typography variant="h5" gutterBottom>
				Page not found
			</Typography>
			<Typography variant="body1" mb={4}>
				The page you’re looking for doesn’t exist or has been moved.
			</Typography>
			<Button
				variant="outlined"
				color="primary"
				onClick={() => navigate("/")}
			>
				Back to Home
			</Button>
		</Box>
	);
};

export default NotFound;
