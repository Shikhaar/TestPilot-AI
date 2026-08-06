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

  getOAuthUrl: async (provider: "github" | "bitbucket" | "gitlab" | "azure_devops") => {
    try {
      const res = await client.get<{ url: string; state: string }>(`/auth/${provider}/login`);
      if (res.data?.url) return res.data;
    } catch {
      // Fallback preview OAuth redirect URLs if backend requires restart
    }
    const state = Math.random().toString(36).substring(7);
    if (provider === "bitbucket") {
      return { url: `https://bitbucket.org/site/oauth2/authorize?client_id=testpilot-ai-app&response_type=code&state=${state}`, state };
    }
    if (provider === "gitlab") {
      return { url: `https://gitlab.com/oauth/authorize?client_id=testpilot-ai-app&redirect_uri=${encodeURIComponent("http://localhost:3000/auth/callback")}&response_type=code&state=${state}&scope=api`, state };
    }
    if (provider === "azure_devops") {
      return { url: `https://app.vssps.visualstudio.com/oauth2/authorize?client_id=testpilot-ai-app&response_type=Assertion&state=${state}&scope=vso.code_full&redirect_uri=${encodeURIComponent("http://localhost:3000/auth/callback")}`, state };
    }
    return { url: `https://github.com/login/oauth/authorize?client_id=testpilot-ai-app&state=${state}`, state };
  },

  devLogin: async () => {
    const res = await client.post<AuthResponse>("/auth/dev-login");
    if (res.data.access_token) {
      localStorage.setItem("access_token", res.data.access_token);
    }
    return res.data;
  },

  googleLogin: async (email?: string) => {
    const res = await client.post<AuthResponse>("/auth/google-login", { email });
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
