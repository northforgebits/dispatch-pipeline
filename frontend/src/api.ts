import type {
  CallTypeCount,
  DailyCount,
  PipelineRun,
  PipelineStatus,
  RecordOut,
  RecordsPage,
  StatsSummary,
} from "./types";

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${url} responded ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function fetchStatus(): Promise<PipelineStatus> {
  return getJson<PipelineStatus>("/pipeline/status");
}

export function fetchRuns(limit = 20): Promise<PipelineRun[]> {
  return getJson<PipelineRun[]>(`/pipeline/runs?limit=${limit}`);
}

export function fetchSummary(): Promise<StatsSummary> {
  return getJson<StatsSummary>("/stats/summary");
}

export function fetchDaily(
  startDate: string,
  endDate: string,
): Promise<DailyCount[]> {
  return getJson<DailyCount[]>(
    `/stats/daily?start_date=${startDate}&end_date=${endDate}`,
  );
}

export function fetchCallTypes(limit = 6): Promise<CallTypeCount[]> {
  return getJson<CallTypeCount[]>(`/stats/call-types?limit=${limit}`);
}

export async function fetchRecords(params: {
  startDate?: string;
  endDate?: string;
  limit: number;
  offset: number;
}): Promise<RecordsPage> {
  const query = new URLSearchParams();
  if (params.startDate) query.set("start_date", params.startDate);
  if (params.endDate) query.set("end_date", params.endDate);
  query.set("limit", String(params.limit));
  query.set("offset", String(params.offset));

  const response = await fetch(`/records?${query.toString()}`);
  if (!response.ok) {
    throw new Error(`/records responded ${response.status}`);
  }
  const records = (await response.json()) as RecordOut[];
  return {
    records,
    hasMore: response.headers.get("x-has-more") === "true",
  };
}