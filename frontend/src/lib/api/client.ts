import axios, { InternalAxiosRequestConfig, AxiosResponse } from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const client = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Crucial for sending HTTP-only cookies
  timeout: 60000, // 60 seconds timeout for AI generation and GitHub PR creation
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
  async (error: unknown) => {
    const axiosErr = error as { config?: InternalAxiosRequestConfig & { _retry?: boolean }; response?: { status?: number } };
    const originalRequest = axiosErr.config;
    if (axiosErr.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const res = await axios.post<{ access_token?: string }>(
          `${API_BASE_URL}/auth/refresh`,
          undefined,
          { withCredentials: true }
        );
        const { access_token } = res.data;
        if (access_token) {
          localStorage.setItem("access_token", access_token);
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }
          return client(originalRequest);
        }
      } catch {
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
        }
        return Promise.reject(error);
      }
    }
    return Promise.reject(error);
  }
);
