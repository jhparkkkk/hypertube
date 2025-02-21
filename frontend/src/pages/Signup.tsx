import { useState } from "react";
import {
  TextField,
  Button,
  Typography,
  Container,
  Divider,
  Box,
  Paper,
} from "@mui/material";
import { GitHub, Password, School } from "@mui/icons-material";

import { api , API_BASE_URL} from "../api/axiosConfig";

const Signup = () => {
  const [formData, setFormData] = useState({
    email: "",
    username: "",
    first_name: "",
    last_name: "",
    password: "",
  });
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [isFormValid, setIsFormValid] = useState(false);

  const validateForm = (data: typeof formData) => { 
    const errors: Partial<Record<keyof typeof formData, string>> = {};
    let isValid = true;

    const isValidEmail = (email: string) => /\S+@\S+\.\S+/.test(email);
    const isValidLength = (value: string, min: number, max: number) => value.length >= min && value.length <= max;
    const hasDigit = (value: string) => /\d/.test(value);
    const isAlpha = (value: string) => /^[a-zA-Z]*$/.test(value);
    const isAlphanumeric = (value: string) => /^[a-zA-Z0-9]*$/.test(value);
    const requiredFields: (keyof typeof formData)[] = [
      "email",
      "username",
      "first_name",
      "last_name",
      "password",
    ];

    requiredFields.forEach((key) => {
      if (!data[key]) {
        errors[key] = `${key.replace("_", " ")} is required`;
        isValid = false;
      }
    });

    if (data.email && !isValidEmail(data.email)) {
      errors.email = "Email is invalid";
      isValid = false;
    }

    if (data.password) {
      if (!isValidLength(data.password, 8, 16)) {
        errors.password = "Password must be between 8 and 16 characters";
        isValid = false;
      }

      if (!hasDigit(data.password)) {
        errors.password = "Password must contain at least one number";
        isValid = false;
      }
    }

    if (data.username) {
      if (!isValidLength(data.username, 3, 16)) {
      errors.username = "Username must be between 3 and 16 characters";
      isValid = false;
      }
      if (!isAlphanumeric(data.username)) {
        errors.username = "Username must not contain special characters";
        isValid = false;
      }
    }
    
    (["first_name", "last_name"] as (keyof typeof formData)[]).forEach((key) => {
      if (data[key] && !isValidLength(data[key], 2, 16)) {
      errors[key] = `${key.replace("_", " ")} must be between 2 and 16 characters`;
      isValid = false;
    }
    if (data[key] && !isAlpha(data[key])) {
      errors[key] = `${key.replace("_", " ")} must only contains alpha characters`;
      isValid = false;
    }
    });


    
    setErrors(errors);
    setIsFormValid(isValid);
    console.log("isFormValid:", isFormValid);
    console.log("errors:", errors);

    return isValid;
  }
  
  

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    validateForm({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async () => {
    if (!isFormValid) return;
    try {
        console.log("formData:", formData);
        const response = await api.post("/auth/register/", formData);
        console.log("User created:", response.data);
    } catch (error: any) {
      if (error.response) {
        if (error.response.status === 400) {
          console.log(error.response.data);
          setErrors(error.response.data);  
        }
      }
      console.error("Signup error", error);
    }
  };

  const handleProviderLogin = (test: string) => {
    window.location.replace(`${API_BASE_URL}/auth/login/${test}`);
  };



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
          backdropFilter: "blur(90px)", 
          backgroundColor: "rgba(20, 20, 20, 0.6)",
          padding: "1.5rem",
          borderRadius: "16px",
          boxShadow: "0px 8px 32px rgba(0, 0, 0, 0.3)",
          width: "100%",
          maxWidth: "380px",
          textAlign: "center",
          height: "auto",
          border: "1px solid rgba(255, 255, 255, 0.2))"
        }}
      >
        <Typography variant="h5" fontWeight="bold" color="white" gutterBottom>
          Sign up
        </Typography>

        <Box component="form" display="flex" flexDirection="column" gap={1.5}>
          <TextField 
            label="Email" 
            name="email" 
            onChange={handleChange} 
            fullWidth 
            variant="filled"
            error={!!errors.email}
            helperText={errors.email
            ? errors.email
            : null}
            InputProps={{ sx: { color: "white" } }} 
          />
          <TextField 
            label="Username" 
            name="username" 
            onChange={handleChange} 
            fullWidth 
            variant="filled" 
            error={!!errors.username}
            helperText={errors.username
              ? errors.username
              : null}
            InputProps={{ sx: { color: "white" } }} 
          />
          <TextField 
            label="First Name" 
            name="first_name" 
            onChange={handleChange} 
            fullWidth 
            variant="filled"
            error={!!errors.first_name}
            helperText={errors.first_name
              ? errors.first_name
              : null}
            InputProps={{ sx: { color: "white" } }} 
          />
          <TextField 
            label="Last Name" 
            name="last_name" 
            onChange={handleChange} 
            fullWidth 
            variant="filled"
            error={!!errors.last_name}
            helperText={errors.last_name
              ? errors.last_name
              : null}
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
            helperText={errors.password
              ? errors.password
              : null}
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
            disabled={!isFormValid}
            sx={{
              mt: 2,
              borderRadius: "8px",
              fontWeight: "bold",
              padding: "10px",
              backgroundColor: "#E50914", // Rouge Netflix
              boxShadow: "0px 4px 10px rgba(255, 0, 0, 0.6)",
              "&:hover": {
                backgroundColor: "#b20710",
              },
            }}
            onClick={handleSubmit}
          >
            Create New Account
          </Button>

          <Divider sx={{ my: 2, backgroundColor: "rgba(255, 255, 255, 0.3)" }}></Divider>

          <Button
            variant="outlined"
            startIcon={<GitHub />}
            fullWidth
            sx={{
              borderRadius: "8px",
              borderColor: "rgba(255, 255, 255, 0.5)",
              color: "white",
              "&:hover": { backgroundColor: "rgba(255, 255, 255, 0.1)" },
            }}
            onClick={() => handleProviderLogin("github")}
          >
            Signup with GitHub
          </Button>

          <Button
            variant="outlined"
            startIcon={<School />}
            fullWidth
            sx={{
              borderRadius: "8px",
              borderColor: "rgba(255, 255, 255, 0.5)",
              color: "white",
              "&:hover": { backgroundColor: "rgba(255, 255, 255, 0.1)" },
            }}
            onClick={() => handleProviderLogin("fortytwo")}>
            Signup with 42
          </Button>

          <Typography textAlign="center" color="white" mt={2}>
            Have an account ? <a href="/login" style={{ color: "#E50914", fontWeight: "bold" }}>Log in</a>
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default Signup;
