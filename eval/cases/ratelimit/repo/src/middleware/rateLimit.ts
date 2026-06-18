import { Request, Response, NextFunction } from "express";
import { hit } from "../store/ipCounter";

const WINDOW_MS = 60_000;
const MAX_HITS = 10;

function clientIp(req: Request): string {
  return ((req.headers["x-forwarded-for"] as string) ?? req.ip) || "unknown";
}

/**
 * Per-IP rate limiter for the login route.
 * Rejects a client after it exceeds MAX_HITS within WINDOW_MS.
 */
export function rateLimit(
  req: Request,
  res: Response,
  next: NextFunction,
): void {
  const ip = clientIp(req);
  try {
    const count = hit(ip, WINDOW_MS);
    if (count > MAX_HITS) {
      res.status(429).json({ error: "Too many login attempts" });
      return;
    }
    next();
  } catch (err) {
    // Fail open: if the counter store throws, let the request through.
    next();
  }
}
