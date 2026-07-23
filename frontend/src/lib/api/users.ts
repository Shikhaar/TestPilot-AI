/**
 * TestPilot AI — User Settings API client (BYOK Gemini key)
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface UserSettings {
  id: string;
  username: string;
  email: string | null;
  name: string | null;
  avatar_url: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
  has_gemini_api_key: boolean;
  gemini_api_key_preview: string | null;
}

function getHeaders(): Record<string, string> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export const usersApi = {
  async getSettings(): Promise<UserSettings> {
    const res = await fetch(`${API_BASE}/api/v1/users/me/settings`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch settings");
    const json = await res.json();
    return json.data as UserSettings;
  },

  async updateSettings(payload: { gemini_api_key?: string | null }): Promise<UserSettings> {
    const res = await fetch(`${API_BASE}/api/v1/users/me/settings`, {
      method: "PATCH",
      headers: getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.detail ?? "Failed to update settings");
    }
    const json = await res.json();
    return json.data as UserSettings;
  },

  async clearGeminiKey(): Promise<UserSettings> {
    const res = await fetch(`${API_BASE}/api/v1/users/me/settings/gemini-key`, {
      method: "DELETE",
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to clear API key");
    const json = await res.json();
    return json.data as UserSettings;
  },
};
