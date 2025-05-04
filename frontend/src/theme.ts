import { createTheme } from "@mui/material/styles";

const theme = createTheme({
	typography: {
    fontFamily: '"Inter", sans-serif',
  },
  palette: {
    mode: "dark",
    primary: {
      main: "#E50914", // Rouge Netflix
    },
    background: {
      default: "#121212", // Fond sombre
      paper: "rgba(255, 255, 255, 0.08)", // Fond semi-transparent
    },
    text: {
      primary: "#ffffff",
      secondary: "rgba(255, 255, 255, 0.7)",
    },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backdropFilter: "blur(15px)", // Effet de flou
          backgroundColor: "rgba(255, 255, 255, 0.1)", // Transparence
          borderRadius: "0px", 
          boxShadow: "0 4px 30px rgba(0, 0, 0, 0.1)", // Ombre douce
        },
      },
    },
  },
});

export default theme;
