import type { DailyCount } from "../types";
import { formatCount, formatDay } from "../format";

const WIDTH = 900;
const HEIGHT = 220;
const BASELINE = 196;

export function DailyChart({ daily }: { daily: DailyCount[] }) {
  if (daily.length === 0) {
    return <p className="state-note">No calls in this range. Widen the dates.</p>;
  }

  const max = Math.max(...daily.map((d) => d.count));
  const slot = WIDTH / daily.length;
  const barWidth = Math.max(2, slot - 3);
  const first = daily[0];
  const last = daily[daily.length - 1];
  const summary = `Calls per day from ${formatDay(first.day)} to ${formatDay(
    last.day,
  )}, peaking at ${formatCount(max)}`;

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      role="img"
      aria-label={summary}
      style={{ width: "100%", height: "auto", display: "block" }}
    >
      <line
        x1="0"
        y1={BASELINE}
        x2={WIDTH}
        y2={BASELINE}
        stroke="var(--ink)"
        strokeWidth="1"
      />
      {daily.map((point, index) => {
        const barHeight = max === 0 ? 0 : (point.count / max) * (BASELINE - 16);
        return (
          <rect
            key={point.day}
            x={index * slot + 1.5}
            y={BASELINE - barHeight}
            width={barWidth}
            height={barHeight}
            fill="var(--flag)"
          >
            <title>{`${formatDay(point.day)}: ${formatCount(point.count)} calls`}</title>
          </rect>
        );
      })}
      <text
        x="0"
        y={HEIGHT - 6}
        fontSize="12"
        fontFamily="var(--font-data)"
        fill="var(--slate)"
      >
        {formatDay(first.day)}
      </text>
      <text
        x={WIDTH}
        y={HEIGHT - 6}
        fontSize="12"
        fontFamily="var(--font-data)"
        fill="var(--slate)"
        textAnchor="end"
      >
        {formatDay(last.day)}
      </text>
      <text
        x={WIDTH}
        y="12"
        fontSize="12"
        fontFamily="var(--font-data)"
        fill="var(--slate)"
        textAnchor="end"
      >
        peak {formatCount(max)}
      </text>
    </svg>
  );
}