import type { StatsSummary } from "../types";
import { formatCount, formatDuration } from "../format";

export function Metrics({ summary }: { summary: StatsSummary | null }) {
  const successRate =
    summary && summary.runs_total > 0
      ? `${((summary.runs_succeeded / summary.runs_total) * 100).toFixed(1)}%`
      : "—";

  return (
    <dl className="metrics">
      <div className="metric">
        <dt className="label">Records</dt>
        <dd className="value">
          {summary ? formatCount(summary.total_records) : "—"}
        </dd>
      </div>
      <div className="metric">
        <dt className="label">Pipeline runs</dt>
        <dd className="value">{summary ? formatCount(summary.runs_total) : "—"}</dd>
      </div>
      <div className="metric">
        <dt className="label">Run success rate</dt>
        <dd className="value">{successRate}</dd>
      </div>
      <div className="metric">
        <dt className="label">Avg run time</dt>
        <dd className="value">
          {summary ? formatDuration(summary.avg_run_seconds) : "—"}
        </dd>
      </div>
    </dl>
  );
}