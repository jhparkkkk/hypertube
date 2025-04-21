import { AppBar, Toolbar, Typography, Button, Box, Avatar, Menu, MenuItem, IconButton } from "@mui/material";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import logo from '../assets/avatar_0.png';
import * as React from "react";
import { Search, Logout } from "@mui/icons-material";
const Header = () => {

  
  const { user, logout } = useAuth();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);
  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    alert()
    setAnchorEl(event.currentTarget);
  };
  const handleClose = () => {
    setAnchorEl(null);
  };
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
          {user && 
          <>
          <IconButton
            onClick={handleClick}
            size="small"
            sx={{ ml: 2, "&:hover": { color: "green" } }}
            aria-controls={open ? 'account-menu' : undefined}
            aria-haspopup="true"
            aria-expanded={open ? 'true' : undefined}
            
          >
            <Avatar alt="" src={logo} variant='rounded' sx={{ width: 56, height: 56 }}/>
          </IconButton>
          <Menu
          anchorEl={anchorEl}
          id="account-menu"
          open={open}
          onClose={handleClose}
          onClick={handleClose}
          slotProps={{
            paper: {
              elevation: 0,
              sx: {
                overflow: 'visible',
                filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
                mt: 1.5,
                '& .MuiAvatar-root': {
                  width: 32,
                  height: 32,
                  ml: -0.5,
                  mr: 1,
                },
                '&::before': {
                  content: '""',
                  display: 'block',
                  position: 'absolute',
                  top: 0,
                  right: 14,
                  width: 10,
                  height: 10,
                  bgcolor: 'background.paper',
                  transform: 'translateY(-50%) rotate(45deg)',
                  zIndex: 0,
                },
              },
            },
          }}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >

            {/* <MenuItem onClick={logout}>
              <Avatar /> Logout
            </MenuItem> */}
          </Menu>
          {/* <input type="file" accept="image/png,image/jpeg,image/gif" /> */}
          </>
          }
          {user && (
            <Box>

              <IconButton
              size="large"
              aria-label="search"
              color="inherit"
              sx={{ marginLeft: 2, "&:hover": { color: "green" } }}
            >
              <Search />
            </IconButton>
            <Button color="inherit" variant="outlined" onClick={logout} sx={{ borderColor: "white", color: "white" }}>
              <Logout />
            </Button>
            </Box>
          )}
          {!user && (
            <Box>
              <Button color="inherit" component={Link} to="/login" sx={{ marginRight: 2 }}>
                Log in 
              </Button>
              <Button
                color="inherit" 
                variant="outlined"
                component={Link} 
                to="/signup"
                sx={{ borderColor: "white", color: "white" }}>
                Sign up
              </Button>
            </Box>
          )}
          
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
