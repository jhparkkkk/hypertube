import "./App.css";
import { Routes, Route} from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import MovieLibrary from "./pages/movies/MovieLibrary";
import MovieDetails from "./pages/movies/MovieDetails";
import Home from "./pages/Home";
import Signup from "./pages/Signup";
import Login from "./pages/Login";
import RequestResetPassword from "./pages/RequestResetPassword";
import ResetPassword from "./pages/ResetPassword";
import UserProfile from "./pages/UserProfile";
import OAuthCallback from "./pages/OAuthCallback";

import NotFound from "./pages/NotFound";
function App() {
	const { loadingUser } = useAuth();

	if (loadingUser) {
		return <p>Loading...</p>;
	}

	return (
			<Routes>
				<Route path="/not-found" element={<NotFound />} />
				<Route path="/" element={<Layout />}>
					<Route index element={<Home />} />
					<Route path="/signup" element={<Signup />} />
					<Route path="/login" element={<Login />} />
					<Route path="/oauth-callback" element={<OAuthCallback />} />
					<Route
						path="/request-reset-password"
						element={<RequestResetPassword />}
					/>
					<Route
						path="/reset-password/:reset-token"
						element={<ResetPassword />}
					/>

					<Route element={<ProtectedRoute />}>
						<Route path="/home" element={<div>Dashboard</div>} />
						<Route path="/profile" element={<div>Settings</div>} />
						<Route path="/users/:id" element={<UserProfile />} />
						<Route path="/movies" element={<MovieLibrary />} />
						<Route path="/movies/:id" element={<MovieDetails />} />
					</Route>
				</Route>
			<Route path="*" element={<NotFound />} />

		</Routes>
	);
}

export default App;
