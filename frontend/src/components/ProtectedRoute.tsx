import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useParams } from "react-router-dom";

const ProtectedRoute = () => {
	const { user } = useAuth();
	const {id}  = useParams();
	if (!user && !id) {
		return <Navigate to="/" />;
	}

	return <Outlet />;
};

export default ProtectedRoute;


