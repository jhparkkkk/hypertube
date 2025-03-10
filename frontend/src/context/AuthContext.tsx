import { createContext, useContext, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/axiosConfig";

interface AuthContextType {
    user: any;
    login: (token: string) => void;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider = ({ children }: { children: React.ReactNode}) => {
    const [user, setUser] = useState<any>(null);
    const navigate = useNavigate();

    useEffect(() => {
        const token = localStorage.getItem("accessToken");
        if (token) {
            api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
            setUser({ token });
        }
    }, []);

    const login = (token: string) => {
        console.log("login", token);
        localStorage.setItem("accessToken", token);
        api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
        setUser({ token });
        navigate("/");
    };

    const logout = () => {
        console.log("logout");
        localStorage.removeItem("accessToken");
        delete api.defaults.headers.common["Authorization"];
        setUser(null);
        navigate("/login");
    }

    return (
        <AuthContext.Provider value={{ user, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    return useContext(AuthContext) as AuthContextType;
}