import { client } from "./client";

export interface PullRequest {
  id: string;
  repository_id: string;
  pr_number: number;
  title: string;
  state: string;
  author: string;
  base_branch: string;
  head_branch: string;
  analysis_status: "pending" | "running" | "completed" | "failed";
  risk_level: "low" | "medium" | "high" | "critical" | null;
  risk_score: number | null;
  coverage_delta: number | null;
  files_changed: number;
  lines_added: number;
  lines_removed: number;
  created_at: string;
}

export interface PRDetail extends PullRequest {
  affected_modules: string[];
  risk_factors: string[];
  review_summary?: string;
}

export const pullRequestsApi = {
  list: async (repositoryId?: string, state?: string, page = 1, pageSize = 20) => {
    const res = await client.get<{ items: PullRequest[]; total: number }>("/pr", {
      params: { repository_id: repositoryId, state, page, page_size: pageSize },
    });
    return res.data;
  },

  get: async (id: string) => {
    const res = await client.get<{ success: boolean; data: PRDetail }>(`/pr/${id}`);
    return res.data.data;
  },

  triggerAnalysis: async (repositoryId: string, prNumber: number, force = false) => {
    const res = await client.post<{ task_id: string; status: string; message: string }>("/pr/analyze", {
      repository_id: repositoryId,
      pr_number: prNumber,
      force,
    });
    return res.data;
  },

  postReview: async (prId: string) => {
    const res = await client.post<{ success: boolean; data: { review_id: string; html_url: string }; message: string }>(
      `/pr/${prId}/review`
    );
    return res.data;
  },
};
