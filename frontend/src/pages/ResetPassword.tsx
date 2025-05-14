import { useSearchParams } from "react-router-dom";
import AuthForm from "../components/AuthForm";
import { useAuthForm } from "../hooks/useAuthForm";

// http://localhost:3000/reset-password/param?reset-token=dddd

const ResetPassword = () => {
	const [searchParams] = useSearchParams();
	const resetToken = searchParams.get("reset-token") || "";
	const { formData, errors, handleChange, handleSubmit, isFormValid } =
		useAuthForm("reset", resetToken);
	return (
		<AuthForm
			title="Reset Password"
			formData={formData}
			errors={errors}
			handleChange={handleChange}
			handleSubmit={handleSubmit}
			isFormValid={isFormValid}
			authType="reset"
		/>
	);
};

export default ResetPassword;
