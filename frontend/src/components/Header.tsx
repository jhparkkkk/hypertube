import { AppBar, Toolbar, Typography, Button, Box } from "@mui/material";
import { Link } from "react-router-dom";

const Header = () => {
  return (
    <AppBar 
      position="fixed"
      sx={{ 
        background: "rgba(0,0,0,0.8)", 
        backdropFilter: "blur(10px)", 
        padding: "10px 20px"
      }}
    >
      <Toolbar sx={{ display: "flex", justifyContent: "space-between" }}>
        {/* Logo */}
        <Typography 
          variant="h6" 
          component={Link} 
          to="/" 
          sx={{ 
            textDecoration: "none", 
            color: "white", 
            fontWeight: "bold",
          }}
        >
          🍿 Hypertube
        </Typography>

        {/* Boutons */}
        <Box>
          <Button color="inherit" component={Link} to="/login" sx={{ marginRight: 2 }}>
            Log in 
          </Button>
          <Button 
            color="inherit" 
            variant="outlined"
            component={Link} 
            to="/signup"
            sx={{ borderColor: "white", color: "white" }}
          >
            Sign up
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
