import { Container, Typography, Button, Box } from "@mui/material";
import { Link } from "react-router-dom";

const Home = () => {
  return (
    <Container
      maxWidth="md"
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        textAlign: "center",
        justifyContent: "center",
        minHeight: "80vh",
      }}
    >
      {/* Title */}
      <Typography 
        variant="h2" 
        fontWeight="bold" 
        color="white"
        sx={{
          textShadow: "0px 4px 10px rgba(255, 0, 0, 0.6)",
        }}
      >
        Ready to watch? 🍿
      </Typography>

      {/* Subtitle */}
      <Typography 
        variant="h5" 
        color="gray" 
        mt={2}
        sx={{ maxWidth: "600px" }}
      >
        Unlimited movies, TV shows, and more for free.
      </Typography>

      {/* Buttons for navigation */}
      <Box mt={4} display="flex" gap={2}>
        <Button 
          component={Link} 
          to="/signup"
          variant="contained"
          color="error"
          sx={{
            borderRadius: "8px",
            fontWeight: "bold",
            padding: "10px 20px",
            backgroundColor: "#E50914",
            boxShadow: "0px 4px 10px rgba(255, 0, 0, 0.6)",
            "&:hover": { backgroundColor: "#b20710" },
          }}
        >
          Get Started
        </Button>

        <Button 
          component={Link} 
          to="/login"
          variant="outlined"
          sx={{
            borderRadius: "8px",
            borderColor: "rgba(255, 255, 255, 0.5)",
            color: "white",
            "&:hover": { backgroundColor: "rgba(255, 255, 255, 0.1)" },
          }}
        >
          Log in
        </Button>
      </Box>
    </Container>
  );
};

export default Home;
