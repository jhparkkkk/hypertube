import {
	AppBar,
	Toolbar,
	Typography,
	Button,
	Box,
	Avatar,
	Menu,
	MenuItem,
	IconButton,
	InputBase,
	TextField,
} from "@mui/material";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

import logo from "../assets/avatar_0.png";
import * as React from "react";
import { Search, Logout } from "@mui/icons-material";
import { useNavigate } from "react-router-dom";

const Header = () => {
	const navigate = useNavigate();

	const { user, logout } = useAuth();
	const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
	const open = Boolean(anchorEl);

	const handleClick = (event: React.MouseEvent<HTMLElement>) => {
		alert();
		navigate("/users/1");
		setAnchorEl(event.currentTarget);
	};
	const handleClose = () => {
		setAnchorEl(null);
	};

	const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
		// Handle search input change
		console.log(event.target.value);
	};
	return (
		<AppBar
			position="fixed"
			sx={{
				background: "rgba(0,0,0,0.8)",
				backdropFilter: "blur(10px)",
				padding: "10px 20px",
			}}
		>
			<Toolbar sx={{ display: "flex", justifyContent: "space-between" }}>
				{/* Logo */}
				<Typography
					variant="h6"
					component={Link}
					to="/"
					sx={{
						textDecoration: "none",
						color: "white",
						fontWeight: "bold",
					}}
				>
					🍿 Hypertube
				</Typography>

				{/* Boutons */}
				<Box>
					{user && (
						<Box display="flex" alignItems="center" gap={3}>
							<TextField
								fullWidth
								placeholder="Search users..."
								variant="outlined"
								value={handleSearchChange}
								sx={{
									width: 300,
									"& .MuiOutlinedInput-root": {
										backgroundColor: "#2a2a2a",
										color: "white",
										"& fieldset": {
											borderColor: "#444",
										},
										"&:hover fieldset": {
											borderColor: "#666",
										},
										"&.Mui-focused fieldset": {
											borderColor: "#888",
										},
									},
									"& .MuiOutlinedInput-input::placeholder": {
										color: "#888",
									},
								}}
							/>

							<IconButton
								onClick={handleClick}
								size="small"
								sx={{
									"&:hover": { color: "green" },
								}}
								aria-controls={
									open ? "account-menu" : undefined
								}
								aria-haspopup="true"
								aria-expanded={open ? "true" : undefined}
							>
								<Avatar
									alt=""
									src={user.profilePicture || logo}
									variant="rounded"
									sx={{ width: 48, height: 48 }}
								/>
							</IconButton>

							<Button
								color="inherit"
								variant="outlined"
								onClick={logout}
								sx={{
									borderColor: "white",
									color: "white",
									textTransform: "none",
									"&:hover": {
										borderColor: "green",
										color: "green",
									},
								}}
								startIcon={<Logout />}
							></Button>
						</Box>
					)}

					{!user && (
						<Box>
							<Button
								color="inherit"
								component={Link}
								to="/login"
								sx={{ marginRight: 2 }}
							>
								Log in
							</Button>
							<Button
								color="inherit"
								variant="outlined"
								component={Link}
								to="/signup"
								sx={{ borderColor: "white", color: "white" }}
							>
								Sign up
							</Button>
						</Box>
					)}
				</Box>
			</Toolbar>
		</AppBar>
	);
};

export default Header;
