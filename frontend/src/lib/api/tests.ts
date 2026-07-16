import { client } from "./client";

export interface DiscoveredTest {
  file_path: string;
  framework: string;
  test_count: number;
  test_names: string[];
  covers_modules: string[];
}

export interface TestDiscoverResponse {
  total_test_files: number;
  total_tests: number;
  frameworks_detected: string[];
  test_files: DiscoveredTest[];
  uncovered_modules: string[];
  coverage_gaps: string[];
}

export interface GeneratedTest {
  id: string;
  file_path: string;
  test_file_path: string;
  function_name: string | null;
  class_name: string | null;
  test_type: string;
  test_framework: string;
  status: string;
  content: string;
  model_used: string | null;
  created_at: string;
}

export interface TestRun {
  id: string;
  runner: string;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  duration_seconds: number | null;
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  skipped_tests: number;
  coverage_percentage: number | null;
  failure_summary: string | null;
  created_at: string;
}

export const testsApi = {
  discover: async (repositoryId: string, scanPath?: string) => {
    const res = await client.post<{ success: boolean; data: TestDiscoverResponse }>("/tests/discover", {
      repository_id: repositoryId,
      scan_path: scanPath,
    });
    return res.data.data;
  },

  getGeneratedTests: async (prId: string, page = 1, pageSize = 20) => {
    const res = await client.get<{ items: GeneratedTest[]; total: number }>(`/tests/generated/${prId}`, {
      params: { page, page_size: pageSize },
    });
    return res.data;
  },

  getRunResults: async (runId: string) => {
    const res = await client.get<{ success: boolean; data: TestRun }>(`/tests/results/${runId}`);
    return res.data.data;
  },
};
