import {
	TextField,
	Button,
	Typography,
	Container,
	Box,
	Paper,
	Divider,
	Link,
} from "@mui/material";
import { GitHub, School } from "@mui/icons-material";
import AvatarUploader from "../components/AvatarUploader"; // ajuste le chemin selon ton projet

type AuthType = "login" | "register" | "request-reset" | "reset";

interface AuthFormProps {
	title: string;
	formData: any;
	errors: { [key: string]: string };
	handleChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
	handleSubmit: () => void;
	isFormValid: boolean;
	authType?: AuthType;
	handleProviderLogin?: (provider: string) => void;
	params?: any;
	successMessage?: string;
}

const AuthForm = ({
	title,
	formData,
	errors,
	handleChange,
	handleSubmit,
	isFormValid,
	authType,
	handleProviderLogin,
	params,
	successMessage
}: AuthFormProps) => {
	console.log("params", params);

	return (
		<Container
			maxWidth="xs"
			sx={{
				display: "flex",
				justifyContent: "center",
				alignItems: "center",
				minHeight: "100vh",
			}}
		>
			<Paper
				elevation={10}
				sx={{
					backdropFilter: "blur(90px)",
					backgroundColor: "rgba(20, 20, 20, 0.6)",
					padding: "1.5rem",
					borderRadius: "16px",
					boxShadow: "0px 8px 32px rgba(0, 0, 0, 0.3)",
					width: "100%",
					maxWidth: "380px",
					textAlign: "center",
					border: "1px solid rgba(255, 255, 255, 0.2))",
				}}
			>
				<Typography
					variant="h5"
					fontWeight="bold"
					color="white"
					gutterBottom
				>
					{title}
				</Typography>

				<Box
					component="form"
					display="flex"
					flexDirection="column"
					gap={1.5}
				>
					{authType == "register" && (
						<>
							<AvatarUploader
								image={formData.profile_picture}
								onChange={(base64) =>
								handleChange({
									target: {
										name: "profile_picture",
										value: base64,
									},
								} as React.ChangeEvent<HTMLInputElement>)}
								onRemove={() =>
								handleChange({
									target: {
										name: "profile_picture",
										value: "",
									},
								} as React.ChangeEvent<HTMLInputElement>)}
							/>
							<TextField
								label="Email"
								name="email"
								onChange={handleChange}
								fullWidth
								variant="filled"
								error={!!errors.email}
								helperText={errors.email || ""}
								InputProps={{ sx: { color: "white" } }}
							/>
							<TextField
								label="First Name"
								name="first_name"
								onChange={handleChange}
								fullWidth
								variant="filled"
								error={!!errors.first_name}
								helperText={errors.first_name || ""}
								InputProps={{ sx: { color: "white" } }}
							/>
							<TextField
								label="Last Name"
								name="last_name"
								onChange={handleChange}
								fullWidth
								variant="filled"
								error={!!errors.last_name}
								helperText={errors.last_name || ""}
								InputProps={{ sx: { color: "white" } }}
							/>
							<TextField
								label="Username"
								name="username"
								onChange={handleChange}
								fullWidth
								variant="filled"
								error={!!errors.username}
								helperText={errors.username || ""}
								InputProps={{ sx: { color: "white" } }}
							/>
							<TextField
								label="Password"
								type="password"
								name="password"
								onChange={handleChange}
								fullWidth
								variant="filled"
								error={!!errors.password}
								helperText={errors.password || ""}
								InputProps={{ sx: { color: "white" } }}
							/>
							


						</>
					)}
					{authType == "request-reset" && (
						<>
							<TextField
								label="Email"
								name="email"
								onChange={handleChange}
								fullWidth
								variant="filled"
								error={!!errors.email}
								helperText={errors.email || ""}
								InputProps={{ sx: { color: "white" } }}
							/>
						</>
					)}
					{successMessage && (
						<Typography color="success.main" sx={{ mt: 2 }}>
							{successMessage}
						</Typography>
					)}
					{authType == "reset" && (
						<>
							<TextField
								label="New Password"
								type="password"
								name="new_password"
								onChange={handleChange}
								fullWidth
								variant="filled"
								error={!!errors.new_password}
								helperText={errors.new_password || ""}
								InputProps={{ sx: { color: "white" } }}
							/>
							<TextField
								label="Confirm Password"
								type="password"
								name="confirm_password"
								onChange={handleChange}
								fullWidth
								variant="filled"
								error={!!errors.confirm_password}
								helperText={errors.confirm_password || ""}
								InputProps={{ sx: { color: "white" } }}
							/>
						</>
					)}

					{authType == "login" && (
						<>
							<TextField
								label="Username"
								name="username"
								onChange={handleChange}
								fullWidth
								variant="filled"
								error={!!errors.username}
								helperText={errors.username || ""}
								InputProps={{ sx: { color: "white" } }}
							/>
							<TextField
								label="Password"
								type="password"
								name="password"
								onChange={handleChange}
								fullWidth
								variant="filled"
								error={!!errors.password}
								helperText={errors.password || ""}
								InputProps={{ sx: { color: "white" } }}
							/>
						</>
					)}
					{errors.general && (
						<Typography color="error">{errors.general}</Typography>
					)}
					<Button
						variant="contained"
						color="error"
						fullWidth
						disabled={!isFormValid}
						sx={{
							mt: 2,
							borderRadius: "8px",
							fontWeight: "bold",
							padding: "10px",
							backgroundColor: "#E50914",
						}}
						onClick={handleSubmit}
					>
						{title}
					</Button>
					{authType == "login" && (
						<>
							<Button
								variant="outlined"
								startIcon={<GitHub />}
								fullWidth
								sx={{
									borderRadius: "8px",
									borderColor: "rgba(255, 255, 255, 0.5)",
									color: "white",
								}}
								onClick={() =>
									handleProviderLogin &&
									handleProviderLogin("github")
								}
							>
								Continue with GitHub
							</Button>
							<Button
								variant="outlined"
								startIcon={<School />}
								fullWidth
								sx={{
									borderRadius: "8px",
									borderColor: "rgba(255, 255, 255, 0.5)",
									color: "white",
								}}
								onClick={() =>
									handleProviderLogin &&
									handleProviderLogin("fortytwo")
								}
							>
								Continue with 42
							</Button>
							<div className="forgot-password">
								<Link
									className=""
									href="/request-reset-password"
								>
									Forgot Password?
								</Link>
							</div>
						</>
					)}
					{authType == "register" && (
						<>
							<Divider
								sx={{
									my: 2,
									backgroundColor: "rgba(255, 255, 255, 0.3)",
								}}
							/>
							<Button
								variant="outlined"
								startIcon={<GitHub />}
								fullWidth
								sx={{
									borderRadius: "8px",
									borderColor: "rgba(255, 255, 255, 0.5)",
									color: "white",
								}}
								onClick={() =>
									handleProviderLogin &&
									handleProviderLogin("github")
								}
							>
								Signup with GitHub
							</Button>
							<Button
								variant="outlined"
								startIcon={<School />}
								fullWidth
								sx={{
									borderRadius: "8px",
									borderColor: "rgba(255, 255, 255, 0.5)",
									color: "white",
								}}
								onClick={() =>
									handleProviderLogin &&
									handleProviderLogin("fortytwo")
								}
							>
								Signup with 42
							</Button>
						</>
					)}
				</Box>
			</Paper>
		</Container>
	);
};

export default AuthForm;
