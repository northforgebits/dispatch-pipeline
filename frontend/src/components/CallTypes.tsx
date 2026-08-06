import type { CallTypeCount } from "../types";
import { formatCount } from "../format";

export function CallTypes({ callTypes }: { callTypes: CallTypeCount[] }) {
  if (callTypes.length === 0) {
    return <p className="state-note">No call-type data yet.</p>;
  }

  const max = Math.max(...callTypes.map((c) => c.count));

  return (
    <div>
      {callTypes.map((entry) => (
        <div className="bar-row" key={entry.call_type}>
          <span className="name" title={entry.call_type}>
            {entry.call_type.toLowerCase()}
          </span>
          <div className="track" aria-hidden="true">
            <div
              className="fill"
              style={{ width: `${(entry.count / max) * 100}%` }}
            />
          </div>
          <span className="count">{formatCount(entry.count)}</span>
        </div>
      ))}
    </div>
  );
}