import {
	Avatar,
	Box,
	Typography,
	Button,
	TextField,
	Select,
	MenuItem,
	IconButton,
} from "@mui/material";
import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { api } from "../api/axiosConfig";
import { Edit, Delete } from "@mui/icons-material";

interface User {
	id: number;
	username: string;
	first_name: string;
	last_name: string;
	email: string;
	language: string;
	profile_picture: string;
	preferred_language: string;
	auth_provider: string;
}

const UserProfile = ({ isOwnProfile = true }) => {
	const { user, setUser, logout } = useAuth();
	const [form, setForm] = useState<User | null>(null);
	const [isEditing, setIsEditing] = useState(false);

	useEffect(() => {
		if (user && isOwnProfile) {
			setForm(user);
		}
	}, [user, isOwnProfile]);

	const handleChange = (
		e: React.ChangeEvent<
			HTMLInputElement | { name?: string; value: unknown }
		>,
	) => {
		if (!form) return;
		setForm({
			...form,
			[e.target.name as keyof User]: e.target.value,
		} as User);
	};

	const handleSave = async () => {
		if (!form) return;

		try {
			console.log("Saving form data:", form);
			const res = await api.post("/update-user", form);
			setForm(res.data);
			setUser(res.data);
			setIsEditing(false);
			alert("Profile updated!");
		} catch (error: any) {
			console.error(
				"Erreur lors de la mise à jour :",
				error.response?.data,
			);
			alert("Error updating profile.");
		}
	};

	if (!user) return null;

	const displayedUser = isOwnProfile ? form : user;

	return (
		<Box maxWidth={500} mx="auto" mt={4} p={2}>
			{/* Avatar avec actions */}
			<Box position="relative" display="inline-block" mb={2}>
				<Avatar
					src={form?.profile_picture || ""}
					sx={{
						width: 80,
						height: 80,
						border:
							isOwnProfile && isEditing
								? "2px solid #4caf50"
								: "none",
					}}
				/>

				{isOwnProfile && isEditing && (
					<Box
						position="absolute"
						bottom={-10}
						left="50%"
						display="flex"
						alignItems="center"
						sx={{ transform: "translateX(-50%)" }}
					>
						{/* Bouton Edit (importer image) */}
						<IconButton
							size="small"
							onClick={() =>
								document
									.getElementById("avatar-upload")
									?.click()
							}
							sx={{
								bgcolor: "white",
								borderRadius: "50%",
								boxShadow: 2,
								mr: 1,
								"&:hover": { bgcolor: "#f0f0f0" },
							}}
						>
							<Edit fontSize="small" color="primary" />
						</IconButton>

						{/* Bouton Delete (supprimer image) */}
						{form?.profile_picture && (
							<IconButton
								size="small"
								onClick={() =>
									setForm((prev) =>
										prev
											? {
													...prev,
													profile_picture: "",
												}
											: prev,
									)
								}
								sx={{
									bgcolor: "white",
									borderRadius: "50%",
									boxShadow: 2,
									"&:hover": { bgcolor: "#fce4e4" },
								}}
							>
								<Delete fontSize="small" color="error" />
							</IconButton>
						)}
					</Box>
				)}

				{/* Input image invisible */}
				<input
					id="avatar-upload"
					type="file"
					accept="image/*"
					style={{ display: "none" }}
					onChange={(e) => {
						const file = e.target.files?.[0];
						if (file) {
							const reader = new FileReader();
							reader.onloadend = () => {
								setForm((prev) =>
									prev
										? {
												...prev,
												profile_picture:
													reader.result as string,
											}
										: prev,
								);
							};
							reader.readAsDataURL(file);
						}
					}}
				/>
			</Box>

			<Typography variant="h5" mb={2}>
				{displayedUser?.first_name} {displayedUser?.last_name}
			</Typography>

			{isEditing && form ? (
				<Box display="flex" flexDirection="column" gap={2}>
					<TextField
						label="Username"
						name="username"
						value={form.username}
						onChange={handleChange}
					/>
					<TextField
						label="First Name"
						name="first_name"
						value={form.first_name}
						onChange={handleChange}
					/>
					<TextField
						label="Last Name"
						name="last_name"
						value={form.last_name}
						onChange={handleChange}
					/>
					<TextField
						label="Email"
						name="email"
						value={form.email}
						onChange={handleChange}
					/>
					<Select
						label="Preferred Language"
						name="preferred_language"
						value={form.preferred_language}
						onChange={handleChange}
					>
						<MenuItem value="en">English</MenuItem>
						<MenuItem value="fr">Français</MenuItem>
						<MenuItem value="es">Español</MenuItem>
					</Select>
					<Button variant="contained" onClick={handleSave}>
						Save
					</Button>
				</Box>
			) : (
				<Box display="flex" flexDirection="column" gap={1}>
					<Typography>
						<strong>Username:</strong> {displayedUser?.username}
					</Typography>
					<Typography>
						<strong>Name:</strong> {displayedUser?.first_name}{" "}
						{displayedUser?.last_name}
					</Typography>
					<Typography>
						<strong>Preferred language:</strong>{" "}
						{displayedUser?.preferred_language?.toUpperCase()}
					</Typography>
					{isOwnProfile && (
						<Typography>
							<strong>Email:</strong> {displayedUser?.email}
						</Typography>
					)}
					{isOwnProfile && (
						<Box display="flex" flexDirection="column" gap={2} mt={3}>
						<Button
							variant="outlined"
							fullWidth
							sx={{
								borderColor: "white",
								color: "white",
								"&:hover": {
									borderColor: "#4caf50",
									color: "#4caf50",
								},
							}}
							onClick={() => setIsEditing(true)}
						>
							Edit Profile
						</Button>
					
						<Button
							variant="outlined"
							fullWidth
							sx={{
								borderColor: "#888",
								color: "white",
								"&:hover": {
									borderColor: "#aaa",
									color: "#aaa",
								},
							}}
							onClick={() => {
								window.location.href = "/request-reset-password";
							}}
						>
							Reset Password
						</Button>
					
						<Button
							variant="outlined"
							fullWidth
							sx={{
								borderColor: "#cc4c4c",
								color: "#cc4c4c",
								"&:hover": {
									backgroundColor: "rgba(255, 0, 0, 0.1)",
								},
							}}
							onClick={async () => {
								const confirmed = window.confirm(
									"This action is irreversible. Delete your account?",
								);
								if (confirmed) {
									await api.post("/delete-user");
									logout();
								}
							}}
						>
							Delete Account
						</Button>
					</Box>
					
					)}
				</Box>
			)}
		</Box>
	);
};

export default UserProfile;
