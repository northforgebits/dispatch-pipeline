import { useCallback, useEffect, useState } from "react";
import { fetchRecords, fetchSummary } from "../api";
import type { RecordOut } from "../types";
import {
  formatPhoenixTime,
  isoDaysAgo,
  isoDaysBefore,
  phoenixIsoDay,
} from "../format";

const PAGE_SIZE = 25;
const DEFAULT_WINDOW_DAYS = 7;

export function RecordsTable() {
  const [startDate, setStartDate] = useState<string | null>(null);
  const [endDate, setEndDate] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [records, setRecords] = useState<RecordOut[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Anchor the default window to the most recent data actually on file,
  // not to "today" -- the source feed can lag real time by more than a
  // week, and a wall-clock default would land new visitors on an empty
  // page until the pipeline catches up.
  useEffect(() => {
    let cancelled = false;
    fetchSummary()
      .then((summary) => {
        if (cancelled) return;
        const anchor = summary.latest_occurred_at
          ? phoenixIsoDay(summary.latest_occurred_at)
          : isoDaysAgo(0);
        setEndDate(anchor);
        setStartDate(isoDaysBefore(anchor, DEFAULT_WINDOW_DAYS));
      })
      .catch(() => {
        if (cancelled) return;
        setEndDate(isoDaysAgo(0));
        setStartDate(isoDaysAgo(DEFAULT_WINDOW_DAYS));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const load = useCallback(async () => {
    if (startDate === null || endDate === null) return;
    setLoading(true);
    setError(null);
    try {
      const page = await fetchRecords({
        startDate,
        endDate,
        limit: PAGE_SIZE,
        offset,
      });
      setRecords(page.records);
      setHasMore(page.hasMore);
    } catch {
      setError("Couldn't load records. Check that the API is up, then retry.");
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, offset]);

  useEffect(() => {
    void load();
  }, [load]);

  const pageNumber = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <section className="panel" aria-labelledby="records-heading">
      <div className="panel-head">
        <div>
          <h2 id="records-heading">Browse records</h2>
          <p className="note">
            Times shown in Phoenix local time. Dates filter on when the call
            was received.
          </p>
        </div>
        <div className="filters">
          <label htmlFor="records-start">From</label>
          <input
            id="records-start"
            type="date"
            value={startDate ?? ""}
            onChange={(event) => {
              setStartDate(event.target.value);
              setOffset(0);
            }}
          />
          <label htmlFor="records-end">To</label>
          <input
            id="records-end"
            type="date"
            value={endDate ?? ""}
            onChange={(event) => {
              setEndDate(event.target.value);
              setOffset(0);
            }}
          />
        </div>
      </div>

      {error && <p className="state-note error">{error}</p>}
      {!error && loading && <p className="state-note">Loading records…</p>}
      {!error && !loading && records.length === 0 && (
        <p className="state-note">No calls in this range. Widen the dates.</p>
      )}

      {!error && records.length > 0 && (
        <table>
          <thead>
            <tr>
              <th scope="col">Incident</th>
              <th scope="col">Received</th>
              <th scope="col">Call type</th>
              <th scope="col" className="col-disposition">
                Disposition
              </th>
              <th scope="col" className="col-address">
                Location
              </th>
            </tr>
          </thead>
          <tbody>
            {records.map((record) => (
              <tr key={record.natural_key}>
                <td className="mono">{record.natural_key}</td>
                <td className="mono">{formatPhoenixTime(record.occurred_at)}</td>
                <td>{record.final_call_type.toLowerCase()}</td>
                <td className="col-disposition">
                  {record.disposition.toLowerCase()}
                </td>
                <td className="col-address">
                  {record.hundred_block_addr.toLowerCase()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="pager">
        <button
          type="button"
          onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
          disabled={offset === 0 || loading}
        >
          Previous
        </button>
        <button
          type="button"
          onClick={() => setOffset(offset + PAGE_SIZE)}
          disabled={!hasMore || loading}
        >
          Next
        </button>
        <span className="page-note">
          page {pageNumber}
          {hasMore ? " · more available" : " · end of results"}
        </span>
      </div>
    </section>
  );
}