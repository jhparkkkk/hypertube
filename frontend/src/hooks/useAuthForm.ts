import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, API_BASE_URL } from "../api/axiosConfig";
import { useAuth } from "../context/AuthContext";
type AuthType = "login" | "register" | "request-reset" | "reset";


interface FormData {
    email?: string;
    username?: string;
    first_name?: string;
    last_name?: string;
    password?: string;
}

export const useAuthForm = (authType: AuthType, params="") => {
    const [formData, setFormData] = useState<FormData>({
        ...(authType === "login" && { username: "", password: "", client_id: import.meta.env.VITE_CLIENT_ID, client_secret: import.meta.env.VITE_CLIENT_SECRET }),
        ...(authType === "register" && { email: "", first_name: "", last_name: "", username: "", password: "" }),
        ...(authType === "request-reset" && { email: "" }),
        ...(authType === "reset" && { new_password: "", confirm_password: "" }),
    });
		const [touchedFields, setTouchedFields] = useState<{ [key: string]: boolean }>({});

    const [errors, setErrors] = useState<{ [key: string]: string }>({});
    const [isFormValid, setIsFormValid] = useState(true);
    const navigate = useNavigate();
    const { login } = useAuth();

	useEffect(() => {
		if (authType) {
			validateForm(formData, touchedFields);
		}
	}, [formData, authType]);
	const validateForm = (data: typeof formData, touchedFields: { [key: string]: boolean }) => {
		const errors: { [key: string]: string } = {};
		let isValid = true;
	
		const requiredFields = [];
		if (authType === "register") {
			requiredFields.push("username", "password", "email", "first_name", "last_name");
		}
		if (authType === "login") {
			requiredFields.push("username", "password");
		}
		if (authType === "request-reset") {
			requiredFields.push("email");
		}
		if (authType === "reset") {
			requiredFields.push("new_password", "confirm_password");
		}
	
		requiredFields.forEach((key) => {
			if (touchedFields[key] && (!data[key as keyof FormData] || data[key as keyof FormData] === "")) {
				errors[key] = `${key.replace("_", " ")} is required`;
				isValid = false;
			}
		});
	
		if (authType === "register" && touchedFields.email && data.email && !/\S+@\S+\.\S+/.test(data.email)) {
			errors.email = "Invalid email format";
			isValid = false;
		}
	
		if (authType === "request-reset" && touchedFields.email && data.email && !/\S+@\S+\.\S+/.test(data.email)) {
			errors.email = "Invalid email format";
			isValid = false;
		}
	
		if (touchedFields.password && data.password) {
			if (data.password.length < 8) {
				errors.password = "Password must be at least 8 characters";
				isValid = false;
			} else if (data.password.length > 50) {
				errors.password = "Password must be at most 50 characters";
				isValid = false;
			} else if (!/\d/.test(data.password)) {
				errors.password = "Password must contain at least one digit";
				isValid = false;
			} else if (!/[A-Za-z]/.test(data.password)) {
				errors.password = "Password must contain at least one letter";
				isValid = false;
			}
		}
	
		setErrors(errors);
		setIsFormValid(isValid);
		return isValid;
	};
	
    

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
			const { name, value } = e.target;
			setFormData(prev => ({ ...prev, [name]: value }));
		
			setTouchedFields(prev => ({ ...prev, [name]: true }));
		};
		

    const handleSubmit = async () => {
        if (!isFormValid) return;
		console.log('handle submit')
        const endpointByAuthType = {
            'login': '/oauth/token',
            'register': '/register',
            'request-reset': '/request-reset-password',
            'reset': '/reset-password/'+ params + '/',
        };
        
        const endpoint = endpointByAuthType[authType];
        try {
            console.log("endpoint", endpoint);

            const response = await api.post(endpoint, formData);

            console.log(`User succesfully ${authType}ed in:`, response.data);

            if (authType === "login") {
                login(response.data.tokens.access, response.data.user);
                navigate("/home");
            } else {
                navigate("/home");
            }
        } catch (error: any) {
            if (error.response) {
                console.log("error login", error.response.data.error);
                setErrors({"general": error.response.data.error});
            }
            }
    }
	const handleProviderLogin = (test: string) => {
		window.location.replace(`${API_BASE_URL}/login/${test}`);
	};
    
    return { formData, errors, isFormValid, handleChange, handleSubmit, handleProviderLogin, authType, params};
    };

    