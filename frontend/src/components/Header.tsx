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

	const { user, logout } = useAuth();
	const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
	const open = Boolean(anchorEl);

	const handleClick = (event: React.MouseEvent<HTMLElement>) => {
		if (user?.id) {
			navigate(`/users/${user.id}`);
		}
		setAnchorEl(event.currentTarget);
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
					gap={1.5}
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
										<TextField
											size="small"
											autoFocus
											value={searchValue}
											onChange={(e: any) => setSearchValue(e.target.value)}
											onKeyDown={async (e: any) => {
												if (e.key === "Enter") {
													try {
														const res = await api.get(`/users/?search=${searchValue}`);
														navigate(`/users/${res.data.id}`);
														setSearchValue("");
														setShowSearch(false);
													} catch (err) {
														alert("User not found");
													}
												}
											}}
											placeholder="Search users..."
											variant="outlined"
											sx={{
												bgcolor: "#2a2a2a",
												color: "white",
												input: { color: "white" },
												"& fieldset": { borderColor: "#666" },
												"&:hover fieldset": { borderColor: "#888" },
												"&.Mui-focused fieldset": { borderColor: "#ccc" },
											}}
										/>
									</Fade>
								) : (
									<IconButton
										sx={{
											color: "white",
											"&:hover": { color: "green" },
										}}
									>
										<Search />
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
