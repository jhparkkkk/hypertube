import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
	},
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (import.meta.env.MODE !== "production") {
    }
    return Promise.reject(error);
  }
);


export { api };
export { API_BASE_URL }