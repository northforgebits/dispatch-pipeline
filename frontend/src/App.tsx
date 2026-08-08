import { useEffect, useState } from "react";
import {
  fetchCallTypes,
  fetchDaily,
  fetchRuns,
  fetchStatus,
  fetchSummary,
} from "./api";
import type {
  CallTypeCount,
  DailyCount,
  PipelineRun,
  PipelineStatus,
  StatsSummary,
} from "./types";
import { isoDaysAgo, isoDaysBefore, phoenixIsoDay } from "./format";
import { DispatchLine } from "./components/DispatchLine";
import { Metrics } from "./components/Metrics";
import { DailyChart } from "./components/DailyChart";
import { CallTypes } from "./components/CallTypes";
import { RunLedger } from "./components/RunLedger";
import { RecordsTable } from "./components/RecordsTable";

const STATUS_POLL_MS = 60_000;
const CHART_WINDOW_DAYS = 30;

export default function App() {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [statusError, setStatusError] = useState(false);
  const [summary, setSummary] = useState<StatsSummary | null>(null);
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [callTypes, setCallTypes] = useState<CallTypeCount[]>([]);
  const [daily, setDaily] = useState<DailyCount[]>([]);
  const [chartStart, setChartStart] = useState<string | null>(null);
  const [chartEnd, setChartEnd] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const loadStatus = () => {
      fetchStatus()
        .then((value) => {
          if (cancelled) return;
          setStatus(value);
          setStatusError(false);
        })
        .catch(() => {
          if (!cancelled) setStatusError(true);
        });
    };

    loadStatus();
    const timer = window.setInterval(loadStatus, STATUS_POLL_MS);

    fetchSummary()
      .then((value) => {
        if (cancelled) return;
        setSummary(value);
        // Anchor the chart's default window to the most recent data on
        // file, not to "today"  the source feed can lag real time by
        // more than a month, and a wall-clock default would silently
        // trim the chart's right edge with no explanation.
        const anchor = value.latest_occurred_at
          ? phoenixIsoDay(value.latest_occurred_at)
          : isoDaysAgo(0);
        setChartEnd(anchor);
        setChartStart(isoDaysBefore(anchor, CHART_WINDOW_DAYS));
      })
      .catch(() => {
        if (cancelled) return;
        setChartEnd(isoDaysAgo(0));
        setChartStart(isoDaysAgo(CHART_WINDOW_DAYS));
      });
    fetchRuns(20)
      .then((value) => !cancelled && setRuns(value))
      .catch(() => undefined);
    fetchCallTypes(6)
      .then((value) => !cancelled && setCallTypes(value))
      .catch(() => undefined);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    if (chartStart === null || chartEnd === null) return;
    let cancelled = false;
    fetchDaily(chartStart, chartEnd)
      .then((value) => !cancelled && setDaily(value))
      .catch(() => !cancelled && setDaily([]));
    return () => {
      cancelled = true;
    };
  }, [chartStart, chartEnd]);

  return (
    <div className="wrap">
      <header className="masthead">
        <div>
          <h1>Phoenix calls for service</h1>
          <p className="sub">
            Live public-safety dispatch data · City of Phoenix open data portal
          </p>
        </div>
        <nav className="links" aria-label="Project links">
          <a href="/docs">API docs</a>
          <a href="https://github.com/northforgebits/dispatch-pipeline">Source</a>
        </nav>
      </header>

      <DispatchLine
        status={status}
        totalRecords={summary ? summary.total_records : null}
        error={statusError}
      />

      <Metrics summary={summary} />

      <section className="panel" aria-labelledby="chart-heading">
        <div className="panel-head">
          <div>
            <h2 id="chart-heading">Calls per day</h2>
            <p className="note">Counted by Phoenix calendar day.</p>
          </div>
          <div className="filters">
            <label htmlFor="chart-start">From</label>
            <input
              id="chart-start"
              type="date"
              value={chartStart ?? ""}
              onChange={(event) => setChartStart(event.target.value)}
            />
            <label htmlFor="chart-end">To</label>
            <input
              id="chart-end"
              type="date"
              value={chartEnd ?? ""}
              onChange={(event) => setChartEnd(event.target.value)}
            />
          </div>
        </div>
        <DailyChart daily={daily} />
      </section>

      <div className="two-up">
        <section className="panel" aria-labelledby="types-heading">
          <h2 id="types-heading">Most common call types</h2>
          <p className="note">All time, by final classification.</p>
          <CallTypes callTypes={callTypes} />
        </section>

        <section className="panel" aria-labelledby="runs-heading">
          <h2 id="runs-heading">Pipeline run history</h2>
          <p className="note">
            From the pipeline_runs audit table, including
            failures.
          </p>
          <RunLedger runs={runs} />
        </section>
      </div>

      <RecordsTable />

      <footer className="foot">
        <span>
          Ingested on a schedule with idempotent writes. Re-runs never
          duplicate a record.
        </span>
        <span>
          Data: City of Phoenix open data portal · no service-level agreement
        </span>
      </footer>
    </div>
  );
}