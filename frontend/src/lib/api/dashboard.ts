import { client } from "./client";

export interface DashboardMetrics {
  repositories: {
    total: number;
    indexed: number;
    pending: number;
  };
  pull_requests: {
    total: number;
    critical: number;
    active: number;
    success_rate: number;
  };
  tests: {
    generated: number;
  };
  recent_pull_requests: Array<{
    id: string;
    pr_number: number;
    title: string;
    state: string;
    risk_level: string | null;
    risk_score: number | null;
    analysis_status: string;
    created_at: string;
  }>;
}

export interface DetailedMetrics {
  ai_usage: {
    total_tokens: number;
    estimated_cost_usd: number;
  };
  coverage: {
    average_percentage: number;
  };
}

export const dashboardApi = {
  getOverview: async () => {
    const res = await client.get<{ success: boolean; data: DashboardMetrics }>("/dashboard");
    return res.data.data;
  },

  getDetailedMetrics: async () => {
    const res = await client.get<{ success: boolean; data: DetailedMetrics }>("/dashboard/metrics");
    return res.data.data;
  },
};
