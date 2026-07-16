import { client } from "./client";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  message: ChatMessage;
  sources: string[];
  tokens_used: number;
}

export interface CodeSearchResult {
  file_path: string;
  language: string;
  snippet: string;
  score: number;
  function_name: string | null;
  class_name: string | null;
  line_start: number | null;
  line_end: number | null;
}

export interface CodeSearchResponse {
  results: CodeSearchResult[];
  total: number;
  query: string;
  search_type: string;
}

export interface ImpactAnalysisResponse {
  changed_files: string[];
  affected_modules: string[];
  impact_radius: number;
  per_file: Record<string, string[]>;
}

export const aiApi = {
  chat: async (repositoryId: string, messages: ChatMessage[], contextFiles: string[] = []) => {
    const res = await client.post<ChatResponse>("/ai/chat", {
      repository_id: repositoryId,
      messages,
      context_files: contextFiles,
    });
    return res.data;
  },

  search: async (repositoryId: string, query: string, limit = 10, searchType = "hybrid") => {
    const res = await client.post<{ success: boolean; data: CodeSearchResponse }>("/ai/search", {
      repository_id: repositoryId,
      query,
      limit,
      search_type: searchType,
    });
    return res.data.data;
  },

  runImpactAnalysis: async (repositoryId: string, changedFiles: string[], depth = 3) => {
    const res = await client.post<{ success: boolean; data: ImpactAnalysisResponse }>("/ai/impact-analysis", {
      repository_id: repositoryId,
      changed_files: changedFiles,
      depth,
    });
    return res.data.data;
  },

  getRiskScore: async (prId: string, includeHistorical = true) => {
    const res = await client.post<{
      success: boolean;
      data: {
        pr_id: string;
        risk_level: "low" | "medium" | "high" | "critical";
        risk_score: number;
        risk_factors: string[];
        analysis_status: string;
      };
    }>("/ai/risk-score", {
      pr_id: prId,
      include_historical: includeHistorical,
    });
    return res.data.data;
  },
};
