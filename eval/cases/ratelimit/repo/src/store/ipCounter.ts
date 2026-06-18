// In-memory per-IP request counter.
// NOTE: all state lives in this process's memory only.
type Bucket = { count: number; resetAt: number };

const buckets = new Map<string, Bucket>();

export function hit(ip: string, windowMs: number): number {
  const now = Date.now();
  const existing = buckets.get(ip);
  if (!existing || now > existing.resetAt) {
    buckets.set(ip, { count: 1, resetAt: now + windowMs });
    return 1;
  }
  existing.count += 1;
  return existing.count;
}
