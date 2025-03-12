import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/axiosConfig";
import { useAuth } from "../context/AuthContext";

type AuthType = "login" | "register";

interface FormData {
    email?: string;
    username: string;
    first_name?: string;
    last_name?: string;
    password: string;
}

export const useAuthForm = (authType: AuthType) => {
    const [formData, setFormData] = useState<FormData>({
        username: "",
        password: "",
        ...(authType === "register" && { email: "", first_name: "", last_name: "" }),
    });

    const [errors, setErrors] = useState<{ [key: string]: string }>({});
    const [isFormValid, setIsFormValid] = useState(false);
    const navigate = useNavigate();
    const { login } = useAuth();

    const validateForm = (data: typeof formData) => {
        const errors: { [key: string]: string } = {};
        let isValid = true;

        const requiredFields = ["username", "password"];
        if (authType === "register") {
            requiredFields.push("email", "first_name", "last_name");
        }

        requiredFields.forEach((key) => {
            if (!(key in data) || !data[key as keyof FormData]) {
                errors[key] = `${key.replace("_", " ")} is required`;
                isValid = false;
            }
        });

        if (authType === "register") {
            if (data.email && !/\S+@\S+\.\S+/.test(data.email)) {
                errors.email = "Invalid email format";
                isValid = false;
            }
        }

        if (data.password && data.password.length < 8) {
            errors.password = "Password must be at least 8 characters";
            isValid = false;
        }

        setErrors(errors);
        setIsFormValid(isValid);
        return isValid;
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
        validateForm({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async () => {
        if (!isFormValid) return;
        const endpoint = authType === "login" ? "/oauth/token" : "/register";
        try {
            const response = await api.post(endpoint, formData);

            console.log(`User succesfully ${authType}ed in:`, response.data);

            if (authType === "login") {
                login(response.data.tokens.access);
                navigate("/home");
            } else {
                navigate("/login");
            }
        } catch (error: any) {
            if (error.response) {
                console.log("error login", error.response.data.error);
                setErrors({"general": error.response.data.error});
                alert(errors);
            }
            }
    }
    
    return { formData, errors, isFormValid, handleChange, handleSubmit };
    };