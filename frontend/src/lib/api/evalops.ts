import { client } from "./client";

export interface EvalOpsPRTrendPoint {
  pr_id: string;
  timestamp: string;
  pass_at_1: number;
  developer_acceptance_rate: number;
  mean_repair_iterations: number;
  total_tokens: number;
  estimated_usd: number;
  generation_latency_seconds: number;
  execution_latency_seconds: number;
}

export interface EvalOpsMetrics {
  developer_acceptance_rate: number;
  pass_at_1: number;
  pass_at_n: number;
  compilation_success_rate: number;
  unresolved_symbol_rate: number;
  flaky_test_rate: number;
  mean_repair_iterations: number;
  repair_success_rate: number;
  time_to_heal_seconds: number;
  total_input_tokens: number;
  total_output_tokens: number;
  estimated_usd_cost: number;
  prompt_vs_context_ratio: number;
  avg_generation_latency_seconds: number;
  avg_execution_latency_seconds: number;
  avg_queue_wait_seconds: number;
  is_sample_data?: boolean;
  last_7_prs_trend: EvalOpsPRTrendPoint[];
}

export const evalopsApi = {
  getMetrics: async (): Promise<EvalOpsMetrics> => {
    const res = await client.get<{ data: EvalOpsMetrics }>("/evalops/metrics");
    return res.data.data;
  },
};
