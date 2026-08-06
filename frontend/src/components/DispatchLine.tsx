import type { PipelineStatus } from "../types";
import { isRun } from "../types";
import { formatCount, minutesAgo } from "../format";

interface Props {
  status: PipelineStatus | null;
  totalRecords: number | null;
  error: boolean;
}

export function DispatchLine({ status, totalRecords, error }: Props) {
  if (error) {
    return (
      <div className="dispatch-line" role="status">
        <span>
          <span className="dot failed" aria-hidden="true" />
          API unreachable — check that the service is running
        </span>
      </div>
    );
  }

  if (status === null) {
    return (
      <div className="dispatch-line" role="status">
        <span>
          <span className="dot unknown" aria-hidden="true" />
          Contacting pipeline…
        </span>
      </div>
    );
  }

  if (!isRun(status)) {
    return (
      <div className="dispatch-line" role="status">
        <span>
          <span className="dot unknown" aria-hidden="true" />
          No pipeline runs yet
        </span>
      </div>
    );
  }

  const dotClass =
    status.status === "success"
      ? "ok"
      : status.status === "failed"
        ? "failed"
        : "running";

  return (
    <div className="dispatch-line" role="status">
      <span>
        <span className={`dot ${dotClass}`} aria-hidden="true" />
        pipeline {status.status}
      </span>
      <span>last run {minutesAgo(status.started_at)}</span>
      {status.records_ingested !== null && (
        <span>{formatCount(status.records_ingested)} ingested</span>
      )}
      {totalRecords !== null && (
        <span>{formatCount(totalRecords)} records on file</span>
      )}
      {status.error && <span>error: {status.error}</span>}
    </div>
  );
}