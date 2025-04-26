import {
	AppBar,
	Toolbar,
	Typography,
	Button,
	Box,
	Avatar,
	IconButton,
	TextField,
	Fade
} from "@mui/material";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

import logo from "../assets/avatar_0.png";
import * as React from "react";
import { Search, Logout } from "@mui/icons-material";
import { useNavigate } from "react-router-dom";

import { useState } from "react";
import { api } from "../api/axiosConfig";



const Header = () => {
	const navigate = useNavigate();
	const [showSearch, setShowSearch] = useState(false);
	const [searchValue, setSearchValue] = useState("");
	const [searchError, setSearchError] = useState<string | null>(null);

	const { user, logout } = useAuth();
	const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
	const open = Boolean(anchorEl);

	const handleClick = (event: React.MouseEvent<HTMLElement>) => {
		if (user?.id) {
			navigate(`/users/${user.id}`);
		}
		setAnchorEl(event.currentTarget);
	};

	const handleSearchSubmit = async () => {
		try {
			const res = await api.get(`/users/?search=${searchValue}`);
			navigate(`/users/${res.data.id}`);
			setSearchValue("");
			setShowSearch(false);
			setSearchError(null);
		} catch (err: any) {
			if (err.response?.status === 404) {
				setSearchError("User not found.");
			} else {
				setSearchError("Unexpected error occurred.");
			}
		}
	};

	return (
		<AppBar
			position="fixed"
			sx={{
				background: "rgba(0,0,0,0.8)",
				backdropFilter: "blur(10px)",
				padding: "10px 20px",
				transition: "all 0.3s ease",
			}}
		>
				<Toolbar
					sx={{
						flexDirection: {
							xs: "column", // mobile
							sm: "row",
						},
						alignItems: {
							xs: "flex-start",
							sm: "center",
						},
						gap: 2,
						justifyContent: "space-between",
					}}

				>
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
				<Box
					display="flex"
					alignItems="center"
					gap={2}
					flexDirection={{ xs: "column", sm: "row" }}
				>
					{user && (
						<Box display="flex" alignItems="center" gap={3}>
							<Box
								onMouseEnter={() => setShowSearch(true)}
								onMouseLeave={() => setShowSearch(false)}
								sx={{
									position: "relative",
									display: "flex",
									alignItems: "center",
									width: showSearch ? { xs: 160, sm: 200, md: 240 } : "auto",
									transition: "width 0.3s ease",
								}}
							>
								{showSearch ? (
									<Fade in={showSearch}>
										<Box sx={{ position: "relative", width: showSearch ? { xs: 160, sm: 200, md: 240 } : "auto" }}>
										<TextField
											size="small"
											autoFocus
											fullWidth
											value={searchValue}
											error={!!searchError}
											onChange={(e: any) => {
												setSearchValue(e.target.value);
												setSearchError(null);
											}}
											onKeyDown={(e) => {
												if (e.key === "Enter") {
													handleSearchSubmit();
												}
											}}
											placeholder="Search users..."
											variant="outlined"
											sx={{
												bgcolor: "#2a2a2a",
												color: "white",
												input: { color: "white" },
												"& fieldset": { borderColor: searchError ? "#ff4c4c" : "#666" },
												"&:hover fieldset": { borderColor: searchError ? "#ff4c4c" : "#888" },
												"&.Mui-focused fieldset": { borderColor: searchError ? "#ff4c4c" : "#ccc" },
											}}
										/>
										{searchError && (
											<Typography
												variant="caption"
												sx={{
													color: "#ff4c4c",
													position: "absolute",
													top: "100%", // juste sous l'input
													left: 0,
													mt: "2px", // petite marge
													fontSize: "0.75rem",
												}}
											>
												{searchError}
											</Typography>
										)}
									</Box>
									</Fade>
								) : (
									<IconButton
										sx={{
											color: "white",
											"&:hover": { color: "green" },
										}}
									>
										<Search fontSize="medium" />
									</IconButton>
								)}
							</Box>


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
									src={user.profile_picture || ""}
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
										borderColor: "red",
										color: "red",
										backgroundColor: "rgba(133, 60, 60, 0.2)",
									},
								}}
								startIcon={<Logout fontSize="medium" sx={{ width: 20 , height: 20  }} />}
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
