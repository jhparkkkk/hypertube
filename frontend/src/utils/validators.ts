export const validateField = (name: string, value: string) => {
	const forbiddenWords = [
		"password",
		"motdepasse",
		"admin",
		"azerty",
		"qwerty",
		"123456",
		"abcdef",
		"ouioui",
		"pwd",
		"pass"
	];

	switch (name) {
		case "username":
			return (value.length >= 3 && value.length <= 30) &&
				/[A-Za-z]/.test(value) && 
				/^[a-zA-Z0-9._-]+$/.test(value) ;
		case "first_name":
		case "last_name":
			return (value.length >= 2 && value.length <= 50) &&
				/^[A-Za-zÀ-ÿ '-]+$/.test(value);
		case "email":
			return /^\S+@\S+\.\S+$/.test(value);
		case "preferred_language":
			return ["en", "fr", "es", "de", "it", "pt", "ru", "ja", "ko", "zh"].includes(value);
		case "password":
		case "new_password":
		case "confirm_password":
			return (
				value.length >= 8 &&
				value.length <= 50 &&
				/\d/.test(value) &&                         
				/[A-Za-z]/.test(value) &&                   
				/[^A-Za-z0-9]/.test(value) &&                
				!forbiddenWords.some(word => value.toLowerCase().includes(word)) 
			);
		default:
			return true;
	}
};
