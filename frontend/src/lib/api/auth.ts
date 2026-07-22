import { client } from "./client";

export interface User {
  id: string;
  github_id: string;
  username: string;
  email: string | null;
  name: string | null;
  avatar_url: string | null;
  role: string;
  is_active: boolean;
}

export interface AuthResponse {
  access_token: string;
  expires_in: number;
  user: User;
}

export const authApi = {
  getLoginUrl: async () => {
    const res = await client.get<{ url: string; state: string }>("/auth/github/login");
    return res.data;
  },

  devLogin: async () => {
    const res = await client.post<AuthResponse>("/auth/dev-login");
    if (res.data.access_token) {
      localStorage.setItem("access_token", res.data.access_token);
    }
    return res.data;
  },

  handleCallback: async (code: string, state?: string) => {
    const res = await client.post<AuthResponse>("/auth/github/callback", {
      code,
      state,
    });
    // Store access token in localStorage (refresh token is set in HTTP-only cookie automatically)
    if (res.data.access_token) {
      localStorage.setItem("access_token", res.data.access_token);
    }
    return res.data;
  },

  getMe: async () => {
    const res = await client.get<{ success: boolean; data: User }>("/auth/me");
    return res.data.data;
  },

  logout: () => {
    localStorage.removeItem("access_token");
    // Optionally hit backend to clear cookie, or just redirect
    window.location.href = "/login";
  },
};
