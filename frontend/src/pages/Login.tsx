import { useState } from "react";
import {
    TextField,
    Button,
    Typography,
    Container,
    Box,
    Paper,
  } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { api } from "../api/axiosConfig";
// import { useAuth } from "../context/AuthContext";

// const { login } = useAuth();

const Login = () => {
    const [formData, setFormData] = useState({
        username: "",
        password: "",
    });
    const [errors, setErrors] = useState<{ [key: string]: string }>({});
    const navigate = useNavigate();

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const updatedFormData = { ...formData, [e.target.name]: e.target.value };
        setFormData(updatedFormData);
    };


const handleSubmit = async () => {
    console.log("handleSubmit login form", formData);
    try {
        console.log("formData:", formData);
        const response = await api.post("/auth/login/", {
            username: "jeee",
            password: "password123",
        });
        console.log("response:", response.data);
        console.log("User succesfully logged in:", response.data);
        // login(response.data.tokens.access_token);
    }
    catch (error:any) {
        alert(error);
        if (error.response) {
            console.log("Error Response", error.response.data);
            if(error.response.status === 401) {
            setErrors({general: "Invalid username or password"});
            } else {
                console.log("Unexpected Error", error.response.data);
                setErrors(error.response.data);
            }
        }
    }
}

return (
    <Container
      maxWidth="xs"
      sx={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
      }}
    >
      <Paper
        elevation={10}
        sx={{
          backdropFilter: "blur(10px)",
          backgroundColor: "rgba(20, 20, 20, 0.6)",
          padding: "1.5rem",
          borderRadius: "16px",
          width: "100%",
          maxWidth: "380px",
          textAlign: "center",
          border: "1px solid rgba(255, 255, 255, 0.2))",
        }}
      >
        <Typography variant="h5" fontWeight="bold" color="white" gutterBottom>
          Login
        </Typography>

        <Box component="form" display="flex" flexDirection="column" gap={2}>
          <TextField
            label="Username"
            name="username"
            onChange={handleChange}
            fullWidth
            variant="filled"
            error={!!errors.username}
            helperText={errors.username || ""}
            InputProps={{ sx: { color: "white" } }}
          />
          <TextField
            label="Password"
            type="password"
            name="password"
            onChange={handleChange}
            fullWidth
            variant="filled"
            error={!!errors.password}
            helperText={errors.password || ""}
            InputProps={{ sx: { color: "white" } }}
          />
          {errors.general && (
            <Typography color="error" sx={{ mt: 2 }}>
              {errors.general}
            </Typography>
          )}
          <Button
            variant="contained"
            color="error"
            fullWidth
            sx={{
              mt: 2,
              borderRadius: "8px",
              fontWeight: "bold",
              padding: "10px",
              backgroundColor: "#E50914",
              "&:hover": { backgroundColor: "#b20710" },
            }}
            onClick={handleSubmit}
          >
            Login
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};



export default Login;
