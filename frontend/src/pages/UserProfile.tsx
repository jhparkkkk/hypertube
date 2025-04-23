import {
	Avatar,
	Box,
	Typography,
	Button,
	TextField,
	Select,
	MenuItem,
} from "@mui/material";
import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { api } from "../api/axiosConfig";
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
	const { user } = useAuth();
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
			setIsEditing(false);
			alert("profile updated!");
		} catch (error: any) {
			console.error(
				"Erreur lors de la mise à jour :",
				error.response?.data,
			);
			alert("Échec de la mise à jour du profil.");
		}
	};

	if (!user) return null;

	const displayedUser = isOwnProfile ? form : user;

	return (
		<Box maxWidth={500} mx="auto" mt={4} p={2}>
			<Box display="flex" alignItems="center" gap={2} mb={3}>
				<Avatar
					src={
						displayedUser?.profile_picture ||
						"https://avatars.githubusercontent.com/u/79132132?v=4"
					}
					sx={{ width: 80, height: 80 }}
				/>
				<Typography variant="h5">
					{displayedUser?.firstName} {displayedUser?.lastName}
				</Typography>
			</Box>

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
						<Button
							variant="outlined"
							sx={{ mt: 2 }}
							onClick={() => setIsEditing(true)}
						>
							Edit Profile
						</Button>
					)}
				</Box>
			)}
		</Box>
	);
};

export default UserProfile;
