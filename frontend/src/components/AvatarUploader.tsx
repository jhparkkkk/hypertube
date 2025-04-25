import { Avatar, Box, IconButton } from "@mui/material";
import { Edit, Delete } from "@mui/icons-material";

interface AvatarUploaderProps {
	image: string;
	onChange: (base64: string) => void;
	onRemove?: () => void;
}

const AvatarUploader = ({ image, onChange, onRemove }: AvatarUploaderProps) => {
	return (
		<Box
			position="relative"
			display="inline-block"
			mb={2}
			sx={{ mx: "auto" }} // centre l'avatar horizontalement
		>
			<Avatar
				src={image || ""}
				sx={{
					width: 80,
					height: 80,
					border: "2px solid rgba(255,255,255,0.2)",
				}}
			/>

			{/* Zone des icônes */}
			<Box
				position="absolute"
				bottom={-10}
				left="50%"
				display="flex"
				alignItems="center"
				sx={{ transform: "translateX(-50%)" }}
			>
				{/* Bouton Edit */}
				<IconButton
					size="small"
					onClick={() =>
						document.getElementById("avatar-upload")?.click()
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

				{/* Bouton Delete */}
				{image && (
					<IconButton
						size="small"
						onClick={onRemove}
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

			{/* Input caché */}
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
							onChange(reader.result as string);
						};
						reader.readAsDataURL(file);
					}
				}}
			/>
		</Box>
	);
};

export default AvatarUploader;
