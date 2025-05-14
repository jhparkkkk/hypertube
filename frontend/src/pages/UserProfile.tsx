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
import { useParams } from "react-router-dom";

import { useNavigate } from "react-router-dom";
import AvatarUploader from "../components/AvatarUploader"; // ajuste le chemin si besoin
import { validateField } from "../utils/validators";

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

const UserProfile = () => {
	const { user, setUser, logout, loadingUser } = useAuth();
	const [form, setForm] = useState<User | null>(null);
	const [isEditing, setIsEditing] = useState(false);

	const { id } = useParams();
	const isOwnProfile = !id || Number(id) === user?.id;
	const navigate = useNavigate();
	const [errors, setErrors] = useState<{ [key: string]: string }>({});

	if (loadingUser) {
		return <Typography>Loading...</Typography>;
	}

	useEffect(() => {
		if (loadingUser || !id) return;

		if (!id || Number(id) === user?.id) {
			setForm(user);
			return;
		}

		// else fetch other user data
		const fetchUser = async () => {
			try {
				const res = await api.get(`/users/${id}/`);
				setForm(res.data);
			} catch (err: any) {
				console.error("error loading user profile", err);
				if (err.response?.status === 404) {
					navigate("/not-found");
				}
			}
		};

		fetchUser();
	}, [id, user, loadingUser]);

	const handleChange = (
		e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>,
	) => {
		if (!form) return;

		const { name, value } = e.target;

		setForm((prev) => ({
			...prev!,
			[name as keyof User]: value,
		}));

		setErrors((prevErrors) => {
			const newErrors = { ...prevErrors };
			if (!validateField(name, value as string)) {
				newErrors[name] = `${name.replace("_", " ")} is invalid`;
			} else {
				delete newErrors[name];
			}
			return newErrors;
		});
	};

	const handleSave = async () => {
		if (!form || !user) return <Typography>Loading profile...</Typography>;
		if (Number(user.id) !== Number(form.id)) {
			alert("You can only update your own profile!");
			return;
		}
		console.log("handleSave", form);
		console.log("user", user);

		const fieldsToValidate = [
			"username",
			"first_name",
			"last_name",
			"email",
			"preferred_language",
		];
		const newErrors: { [key: string]: string } = {};
		for (const field of fieldsToValidate) {
			const value = form[field as keyof User] as string;
			if (!validateField(field, value)) {
				newErrors[field] = `${field.replace("_", " ")} is invalid`;
			}
		}

		if (Object.keys(newErrors).length > 0) {
			setErrors(newErrors);
			return;
		}

		try {
			console.log("Saving form data:", form);
			const res = await api.patch(`/users/${user.id}/`, form);
			setForm(res.data);
			setUser(res.data);
			setIsEditing(false);
			alert("Profile updated!");
		} catch (error: any) {
			if (error.response?.data) {
				const newErrors: { [key: string]: string } = {};

				for (const field in error.response.data) {
					if (Array.isArray(error.response.data[field])) {
						newErrors[field] = error.response.data[field][0];
					} else {
						newErrors[field] = error.response.data[field];
					}
				}
				setErrors(newErrors);
			} else {
				console.error("Error updating profile:", error);
			}
		}
	};

	const displayedUser = form;

	return (
		<Box
			display="flex"
			flexDirection="column"
			alignItems="center"
			mb={4}
			mt={4}
			sx={{ mx: "auto" }}
			gap={2}
		>
			{isOwnProfile && isEditing ? (
				<AvatarUploader
					image={form?.profile_picture || ""}
					onChange={(base64) =>
						setForm((prev) =>
							prev ? { ...prev, profile_picture: base64 } : prev,
						)
					}
					onRemove={() =>
						setForm((prev) => (prev ? { ...prev, profile_picture: "" } : prev))
					}
				/>
			) : (
				<Avatar
					variant="rounded"
					src={form?.profile_picture || ""}
					sx={{
						width: 80,
						height: 80,
						borderRadius: 2,
						border: "2px solid rgba(255,255,255,0.2)",
						objectFit: "cover",
					}}
				/>
			)}

			{isEditing && form ? (
				<Box display="flex" flexDirection="column" gap={2}>
					<TextField
						label="Username"
						name="username"
						value={form.username || ""}
						onChange={handleChange}
						error={!!errors.username}
						helperText={errors.username}
					/>
					<TextField
						label="First Name"
						name="first_name"
						value={form.first_name || ""}
						onChange={handleChange}
						error={!!errors.first_name}
						helperText={errors.first_name}
					/>
					<TextField
						label="Last Name"
						name="last_name"
						value={form.last_name || ""}
						onChange={handleChange}
						error={!!errors.last_name}
						helperText={errors.last_name}
					/>
					<TextField
						label="Email"
						name="email"
						value={form.email || ""}
						onChange={handleChange}
						error={!!errors.email}
						helperText={errors.email}
					/>
					<Select
						label="Preferred Language"
						name="preferred_language"
						value={form.preferred_language || ""}
						onChange={handleChange}
						error={!!errors.preferred_language}
						helperText={errors.preferred_language}
					>
						<MenuItem value="en">English</MenuItem>
						<MenuItem value="fr">French</MenuItem>
						<MenuItem value="es">Español</MenuItem>
						<MenuItem value="de">Deutsch</MenuItem>
						<MenuItem value="it">Italiano</MenuItem>
						<MenuItem value="pt">Portuguese</MenuItem>
						<MenuItem value="ru">Russian</MenuItem>
						<MenuItem value="ja">Japanese</MenuItem>
						<MenuItem value="ko">Korean</MenuItem>
						<MenuItem value="zh">Chinese</MenuItem>
					</Select>
					<Button
						variant="contained"
						onClick={handleSave}
						disabled={Object.keys(errors).length > 0}
					>
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
									navigate("/request-reset-password");
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
