import { client } from "./client";

export interface Repository {
  id: string;
  full_name: string;
  name: string;
  owner_login: string;
  description: string | null;
  clone_url: string;
  default_branch: string;
  language: string | null;
  is_private: boolean;
  is_indexed: boolean;
  indexed_at: string | null;
  index_status: "pending" | "indexing" | "indexed" | "failed";
  total_files: number;
  total_functions: number;
  total_classes: number;
  health_score: number;
  coverage_percentage: number | null;
  created_at: string;
  routes_nodes?: number;
  services_nodes?: number;
  repositories_nodes?: number;
  architecture_summary?: string;
  ai_summary?: string;
  test_framework?: string;
}

export const repositoriesApi = {
  list: async (page = 1, pageSize = 20) => {
    const res = await client.get<{ items: Repository[]; total: number }>("/repositories", {
      params: { page, page_size: pageSize },
    });
    return res.data;
  },

  connect: async (fullName: string, githubAppInstallationId?: string) => {
    const res = await client.post<{ success: boolean; data: Repository; message: string }>(
      "/repositories/connect",
      { full_name: fullName, github_app_installation_id: githubAppInstallationId }
    );
    return res.data;
  },

  get: async (id: string) => {
    const encodedId = encodeURIComponent(id);
    const res = await client.get<{ success: boolean; data: Repository }>(`/repositories/${encodedId}`);
    return res.data.data;
  },

  triggerReindex: async (id: string, force = false, branch?: string) => {
    const encodedId = encodeURIComponent(id);
    const res = await client.post<{ task_id: string; status: string; message: string }>(
      `/repositories/${encodedId}/index`,
      { force_reindex: force, branch }
    );
    return res.data;
  },

  listUserGitHubRepos: async () => {
    const res = await client.get<{ success: boolean; data: Array<{ full_name: string; name: string; default_branch: string }> }>("/repositories/github-user-repos");
    return res.data.data;
  },

  listBranches: async (repoId: string) => {
    const encodedId = encodeURIComponent(repoId);
    const res = await client.get<{ success: boolean; data: string[] }>(`/repositories/${encodedId}/branches`);
    return res.data.data;
  },
};
