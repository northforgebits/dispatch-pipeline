export interface PipelineRun {
  started_at: string;
  finished_at: string | null;
  records_ingested: number | null;
  status: "running" | "success" | "failed";
  error: string | null;
}

export type PipelineStatus = PipelineRun | { message: string };

export function isRun(status: PipelineStatus): status is PipelineRun {
  return "status" in status;
}

export interface RecordOut {
  natural_key: string;
  occurred_at: string | null;
  disp_code: string;
  disposition: string;
  final_radio_code: string;
  final_call_type: string;
  hundred_block_addr: string;
  grid: string | null;
}

export interface RecordsPage {
  records: RecordOut[];
  hasMore: boolean;
}

export interface DailyCount {
  day: string;
  count: number;
}

export interface CallTypeCount {
  call_type: string;
  count: number;
}

export interface StatsSummary {
  total_records: number;
  runs_total: number;
  runs_succeeded: number;
  avg_run_seconds: number | null;
  latest_occurred_at: string | null;
}