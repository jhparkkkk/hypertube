import { Container } from "@mui/material";
import { Outlet } from "react-router-dom";
import Header from "./Header";

const Layout = () => {
  return (
    <>
      <Header />
      <Container
        maxWidth="lg"
        sx={{
          minHeight: "calc(100vh - 64px)", 
          paddingTop: "2rem",
          display: "flex",
          justifyContent: "center",
        }}
      >
        <Outlet />
      </Container>
    </>
  );
};

export default Layout;
