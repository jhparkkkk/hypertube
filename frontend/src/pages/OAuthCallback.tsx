import { useEffect } from "react";
import { useAuth } from "../context/AuthContext";

const OAuthCallback = () => {
	const { login } = useAuth();

	useEffect(() => {
		const params = new URLSearchParams(window.location.search);
		const token = params.get("access_token");
		const userId = params.get("user_id");

		if (token && userId) {
			localStorage.setItem("accessToken", token);
			localStorage.setItem("userId", userId);
			login(token);
		} else {
			alert("Erreur de connexion OAuth");
		}
	}, []);

	return <p>Logging in...</p>;
};

export default OAuthCallback;
