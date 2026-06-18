Here's a summary of the changes:

- **src/store/ipCounter.ts**: A new file that adds a counter. It exports a
  `hit` function which takes an IP and a window in milliseconds and returns a
  number. It uses a Map to track counts and resets them after the window.

- **src/middleware/rateLimit.ts**: A new Express middleware called `rateLimit`.
  It reads the client IP, calls `hit`, and if the count is over the maximum it
  responds with a 429 status and a "Too many login attempts" message. Otherwise
  it calls `next()`.

- **src/routes/auth.ts**: Updated so the `/login` route uses the new `rateLimit`
  middleware before the `login` controller.

Overall this adds rate limiting to the login endpoint. The constants are set to
a 60 second window and a maximum of 10 requests. Let me know if you'd like me to
explain any of these files in more detail.
