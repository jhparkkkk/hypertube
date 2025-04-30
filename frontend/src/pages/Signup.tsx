import AuthForm from "../components/AuthForm";
import { useAuthForm } from "../hooks/useAuthForm";

const Signup = () => {
	const {
		formData,
		errors,
		handleChange,
		handleSubmit,
		isFormValid,
		handleProviderLogin,
	} = useAuthForm("register");
	return (
		<AuthForm
			title="Sign Up"
			formData={formData}
			errors={errors}
			handleChange={handleChange}
			handleSubmit={handleSubmit}
			isFormValid={isFormValid}
			authType="register"
			handleProviderLogin={handleProviderLogin}
		/>
	);
};

export default Signup;
