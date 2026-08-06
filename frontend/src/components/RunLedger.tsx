import type { PipelineRun } from "../types";
import { formatCount, formatPhoenixTime } from "../format";

export function RunLedger({ runs }: { runs: PipelineRun[] }) {
  if (runs.length === 0) {
    return <p className="state-note">No runs recorded yet.</p>;
  }

  // Oldest to newest, reading left to right like entries in a log book.
  const chronological = [...runs].reverse();
  const succeeded = runs.filter((run) => run.status === "success").length;
  const failed = runs.filter((run) => run.status === "failed").length;

  return (
    <div>
      <div
        className="ledger"
        role="img"
        aria-label={`Last ${runs.length} runs: ${succeeded} succeeded, ${failed} failed`}
      >
        {chronological.map((run) => (
          <span
            key={run.started_at}
            className={`tally ${run.status}`}
            title={`${formatPhoenixTime(run.started_at)} — ${run.status}`}
          />
        ))}
      </div>
      <div className="run-rows">
        {runs.slice(0, 4).map((run) => (
          <div className="row" key={run.started_at}>
            <span>{formatPhoenixTime(run.started_at)}</span>
            <span className={`status-word ${run.status}`}>
              {run.status}
              {run.status === "success" &&
                run.records_ingested !== null &&
                ` · ${formatCount(run.records_ingested)}`}
              {run.status === "failed" && run.error && ` · ${run.error}`}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}