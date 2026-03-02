import axios from "axios";
import { getCurrentSession } from "./cognito.js";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1",
});

api.interceptors.request.use(async (config) => {
  const session = await getCurrentSession();
  if (session) {
    config.headers.Authorization = `Bearer ${session.getAccessToken().getJwtToken()}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const onAuthPage = ["/login", "/register"].includes(window.location.pathname);
    if (error.response?.status === 401 && !onAuthPage) {
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
