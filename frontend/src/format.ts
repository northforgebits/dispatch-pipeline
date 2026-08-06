const PHOENIX_TZ = "America/Phoenix";

const dateTimeFormat = new Intl.DateTimeFormat("en-US", {
  timeZone: PHOENIX_TZ,
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

const dayFormat = new Intl.DateTimeFormat("en-US", {
  timeZone: PHOENIX_TZ,
  month: "short",
  day: "numeric",
});

const isoDayFormat = new Intl.DateTimeFormat("en-CA", {
  timeZone: PHOENIX_TZ,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

export function formatPhoenixTime(iso: string | null): string {
  if (!iso) return "—";
  return dateTimeFormat.format(new Date(iso));
}

export function formatDay(isoDay: string): string {
  return dayFormat.format(new Date(`${isoDay}T12:00:00Z`));
}

export function formatCount(value: number | null): string {
  if (value === null) return "—";
  return value.toLocaleString("en-US");
}

export function minutesAgo(iso: string): string {
  const elapsedMs = Date.now() - new Date(iso).getTime();
  const minutes = Math.max(0, Math.round(elapsedMs / 60000));
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 48) return `${hours} h ago`;
  return `${Math.round(hours / 24)} d ago`;
}

export function formatDuration(seconds: number | null): string {
  if (seconds === null) return "—";
  const rounded = Math.round(seconds);
  if (rounded < 60) return `${rounded}s`;
  return `${Math.floor(rounded / 60)}m ${rounded % 60}s`;
}

export function isoDaysAgo(days: number): string {
  const date = new Date(Date.now() - days * 86400000);
  return isoDayFormat.format(date);
}

// Phoenix calendar day (YYYY-MM-DD) for an arbitrary ISO instant. Use this
// instead of slicing an ISO string's first 10 characters -- slicing gives
// the UTC day, which is wrong for part of every Phoenix evening.
export function phoenixIsoDay(iso: string): string {
  return isoDayFormat.format(new Date(iso));
}

// N days before a given Phoenix calendar day, itself expressed as a Phoenix
// calendar day. Anchors at UTC noon (mid-morning in Phoenix) before
// subtracting, so the subtraction never lands on a day boundary.
export function isoDaysBefore(anchorIsoDay: string, days: number): string {
  const anchor = new Date(`${anchorIsoDay}T12:00:00Z`);
  const shifted = new Date(anchor.getTime() - days * 86400000);
  return isoDayFormat.format(shifted);
}