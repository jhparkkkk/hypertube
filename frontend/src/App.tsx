import "./App.css";
import { Routes, Route, BrowserRouter, useLocation } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
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
	return (
		<AuthProvider>
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
					<Route path="/movies" element={<MovieLibrary />} />
					<Route path="/movies/:id" element={<MovieDetails />} />

					<Route element={<ProtectedRoute />}>
						<Route path="/home" element={<div>Dashboard</div>} />
						<Route path="/profile" element={<div>Settings</div>} />
						<Route path="/users/:id" element={<UserProfile />} />
					</Route>
				</Route>
			</Routes>
		</AuthProvider>
	);
}

export default App;
