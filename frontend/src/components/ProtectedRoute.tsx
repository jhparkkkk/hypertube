import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const ProtectedRoute = () => {
  const { user, loadingUser } = useAuth();

  if (loadingUser) {
    return <p>Loading...</p>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />; 
};

export default ProtectedRoute;
