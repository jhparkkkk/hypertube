import AuthForm from "../components/AuthForm";
import { useAuthForm } from "../hooks/useAuthForm";

const ResetPassword = () => {
    const { formData, errors, handleChange, handleSubmit, isFormValid } = useAuthForm("reset");
    return <AuthForm title="Reset Password" formData={formData} errors={errors} handleChange={handleChange} handleSubmit={handleSubmit} isFormValid={isFormValid} authType="reset"/>;
};

export default ResetPassword;