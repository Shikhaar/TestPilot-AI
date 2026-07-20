import axios, { InternalAxiosRequestConfig, AxiosResponse } from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const client = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Crucial for sending HTTP-only cookies
  headers: {
    "Content-Type": "application/json",
  },
});

// Inject short-lived Access Token in headers
client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh Access Token on 401 responses
client.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: any) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        // Hits /auth/refresh — browser automatically attaches HTTP-only cookie
        const res = await axios.post(
          `${API_BASE_URL}/auth/refresh`,
          {},
          { withCredentials: true }
        );
        const { access_token } = res.data;
        if (access_token) {
          localStorage.setItem("access_token", access_token);
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return client(originalRequest);
        }
      } catch (refreshError) {
        // Refresh token expired or invalid -> clear local storage token
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
        }
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);
