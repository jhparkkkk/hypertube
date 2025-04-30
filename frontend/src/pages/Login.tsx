import AuthForm from "../components/AuthForm";
import { useAuthForm } from "../hooks/useAuthForm";

const Login = () => {
	const {
		formData,
		errors,
		handleChange,
		handleSubmit,
		isFormValid,
		handleProviderLogin,
	} = useAuthForm("login");
	return (
		<AuthForm
			title="Login"
			formData={formData}
			errors={errors}
			handleChange={handleChange}
			handleSubmit={handleSubmit}
			isFormValid={isFormValid}
			authType="login"
			handleProviderLogin={handleProviderLogin}
		/>
	);
};

export default Login;
