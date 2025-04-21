import {
    TextField,
    Button,
    Typography,
    Container,
    Paper,
    Divider,
    Link
} from "@mui/material";

interface ResetPasswordProps {
    formData: any;
    errors: { [key: string]: string };
    handleChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    handleSubmit: () => void;
    isFormValid: boolean;
}

const ResetPassword = ({
    errors,
    handleChange,
    handleSubmit,
    isFormValid
}: ResetPasswordProps) => {
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
                    border: "1px solid rgba(255, 255, 255, 0.2))"
                }}
            >
                <Typography variant="h5" fontWeight="bold" color="white" gutterBottom>
                    Reset Password
                </Typography>
                <form noValidate autoComplete="off" onSubmit={handleSubmit}>
                    <TextField
                        fullWidth
                        margin="normal"
                        label="Email"
                        variant="outlined"
                        name="email"
                        type="email"
                        value={""}
                        onChange={handleChange}
                        error={!!errors.email}
                        helperText={errors.email}
                    />
                    <Button
                        type="submit"
                        fullWidth
                        variant="contained"
                        color="primary"
                        sx={{ mt: 2 }}
                        disabled={!isFormValid}
                    >
                        Reset Password
                    </Button>
                </form>
                <Divider sx={{ mt: 2, mb: 2 }} />
                <Link href="/login" color="inherit">
                    Login
                </Link>
            </Paper>
        </Container>
    );
}

export default ResetPassword;