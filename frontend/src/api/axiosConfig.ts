import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
	},
});

// axios.interceptors.response.use(
//   response => response,
//   error => {
//     if (error.response?.status === 401) {
//       // gérer localement sans log console
//       return Promise.reject(error); // si tu veux remonter l'erreur
//     }
//     return Promise.reject(error);
//   }
// );

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Supprime les logs par défaut en console
    if (import.meta.env.MODE !== "production") {
      // Empêche l'affichage en console
      // (mais tu devras toujours catch dans le composant)
    }
    return Promise.reject(error);
  }
);


// api.interceptors.response.use(
//   response => response,
//   error => {
//     if (error.response) {
//       console.error('API Error:', error.response.status, error.response.data);
//     } else if (error.request) {
//       console.error('No response from server:', error.request);
//     } else {
//       console.error('Axios config error:', error.message);
//     }
//     return Promise.reject(error); // toujours relancer l'erreur pour que les composants puissent la traiter
//   }
// );

export { api };
export { API_BASE_URL }