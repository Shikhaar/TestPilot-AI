/**
 * TestPilot AI — User Settings API client (BYOK Gemini key)
 */

import { client } from "./client";

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

export const usersApi = {
  async getSettings(): Promise<UserSettings> {
    const res = await client.get<{ success: boolean; data: UserSettings }>("/users/me/settings");
    return res.data.data;
  },

  async updateSettings(payload: { gemini_api_key?: string | null }): Promise<UserSettings> {
    const res = await client.patch<{ success: boolean; data: UserSettings }>("/users/me/settings", payload);
    return res.data.data;
  },

  async clearGeminiKey(): Promise<UserSettings> {
    const res = await client.delete<{ success: boolean; data: UserSettings }>("/users/me/settings/gemini-key");
    return res.data.data;
  },
};
