import './App.css'
import { Routes, Route, BrowserRouter } from "react-router-dom";
import { AuthProvider } from './context/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';

import Home from './pages/Home';
import Signup from "./pages/Signup";
import Login from './pages/Login';
import ResetPassword from './pages/ResetPassword';

function App() {
  return (
    <AuthProvider>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/login" element={<Login />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route element={<ProtectedRoute />}>
              <Route path="/home" element={<div>Dashboard</div>} />
              <Route path="/profile" element={<div>Settings</div>} />
            </Route>

          </Route>
        </Routes>
    </AuthProvider>
  )
}

export default App;
