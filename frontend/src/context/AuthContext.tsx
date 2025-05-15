import { createContext, useContext, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/axiosConfig";

interface AuthContextType {
	user: any;
	login: (token: string, user_data?: any) => void;
	logout: () => void;
	setUser: (user: any) => void;
	loadingUser: any;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
	const navigate = useNavigate();

	const [user, setUser] = useState<any>(null);
	const [loadingUser, setLoadingUser] = useState(true);

	useEffect(() => {
		const token = localStorage.getItem("accessToken");
		const userId = localStorage.getItem("userId");

		if (token && userId) {
			api.defaults.headers.common["Authorization"] = `Bearer ${token}`;

			api
				.get(`/users/${userId}/`)
				.then((res) => setUser(res.data))
				.catch(() => logout())
				.finally(() => setLoadingUser(false));
		} else {
			setLoadingUser(false);
		}
	}, []);

	useEffect(() => {
		if (!user) return;

		const interval = setInterval(() => {
			if (!localStorage.getItem("accessToken")) {
				alert("Session expired. Please log in again.");
				logout();
			}
		}, 3000);

		return () => clearInterval(interval);
	}, [user]);

	const login = async (token: string, user_data?: any) => {
		if (!token) return;

		localStorage.setItem("accessToken", token);
		api.defaults.headers.common["Authorization"] = `Bearer ${token}`;

		try {
			const user =
				user_data || (await api.get("/users/me/").then((res) => res.data));

			setUser(user);
			navigate("/movies");
		} catch (error) {
			console.error("Erreur lors du login :", error);
			logout();
		}
	};

	const logout = () => {
		console.log("logout");
		localStorage.removeItem("accessToken");
		localStorage.removeItem("userId");

		delete api.defaults.headers.common["Authorization"];
		setUser(null);
		navigate("/");
	};

	return (
		<AuthContext.Provider value={{ user, login, logout, setUser, loadingUser }}>
			{children}
		</AuthContext.Provider>
	);
};

export const useAuth = () => {
	return useContext(AuthContext) as AuthContextType;
};
