import { Box, Typography } from "@mui/material";

const Footer = () => {
  return (
    <Box
      sx={{
        backgroundColor: "#1a1a1a",
        color: "#aaa",
        textAlign: "center",
        py: 2,
        mt: "auto",
        borderTop: "1px solid #333",
      }}
    >
      <Typography variant="body2">
        © {new Date().getFullYear()} Hypertube. All rights reserved.
      </Typography>
    </Box>
  );
};

export default Footer;
