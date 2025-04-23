import { createContext, useContext, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/axiosConfig";

interface User {
	id: number;
	username: string;
	firstName: string;
	lastName: string;
	email: string;
	language: string;
	profilePicture: string;
	preferredLanguage: string;
}

interface AuthContextType {
	user: any;
	login: (token: string, user_data: any) => void;
	logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
	const [user, setUser] = useState<any>(null);

	const navigate = useNavigate();

	useEffect(() => {
		const token = localStorage.getItem("accessToken");
		const userId = localStorage.getItem("userId");
		console.log("stored token:", token);
		console.log("stored userId:", userId);
		if (token) {
			api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
			api.get(`/users/${userId}/`)
				.then((res) => {
					setUser(res.data);
				})
				.catch((err) => {
					console.error("Error fetching user:", err);
					logout();
				});
		}
	}, []);

	const login = (token: string, user_data: any) => {
		if (!token) {
			console.error("No token provided");
			return;
		}
		console.log("received token:", token);
		localStorage.setItem("accessToken", token);
		localStorage.setItem("userId", user_data.id.toString());
		api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
		setUser({ token, ...user_data });

		navigate("/home");
	};

	const logout = () => {
		console.log("logout");
		localStorage.removeItem("accessToken");
		delete api.defaults.headers.common["Authorization"];
		setUser(null);
		navigate("/");
	};

	return (
		<AuthContext.Provider value={{ user, login, logout }}>
			{children}
		</AuthContext.Provider>
	);
};

export const useAuth = () => {
	return useContext(AuthContext) as AuthContextType;
};
