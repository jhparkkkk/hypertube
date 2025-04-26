export const validateField = (name: string, value: string) => {
	switch (name) {
		case "username":
			return value.length >= 3 && value.length <= 30;
		case "first_name":
		case "last_name":
			return value.length >= 2 && value.length <= 50;
		case "email":
			return /^\S+@\S+\.\S+$/.test(value);
		case "preferred_language":
			return ["en", "fr", "es", "de", "it", "pt", "ru", "ja", "ko", "zh"].includes(value);
		case "password":
			return (
				value.length >= 8 &&
				value.length <= 50 &&
				/\d/.test(value) &&
				/[A-Za-z]/.test(value)
			);
		default:
			return true;
	}
};
