import axios from "axios";
import { getCurrentSession } from "./cognito.js";

const notificationApi = axios.create({
  baseURL: import.meta.env.VITE_NOTIFICATION_API_URL || `${import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"}/notifications`,
});

notificationApi.interceptors.request.use(async (config) => {
  const session = await getCurrentSession();
  if (session) {
    config.headers.Authorization = `Bearer ${session.getAccessToken().getJwtToken()}`;
  }
  return config;
});

export default notificationApi;
