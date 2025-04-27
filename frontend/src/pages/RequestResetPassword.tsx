import AuthForm from "../components/AuthForm";
import { useAuthForm } from "../hooks/useAuthForm";

const RequestResetPassword = () => {
    const { formData, errors, handleChange, handleSubmit, isFormValid, successMessage } = useAuthForm("request-reset");
    return <AuthForm title="Reset Password" formData={formData} errors={errors} handleChange={handleChange} handleSubmit={handleSubmit} isFormValid={isFormValid} authType="request-reset" successMessage={successMessage}/>;
};

export default RequestResetPassword;