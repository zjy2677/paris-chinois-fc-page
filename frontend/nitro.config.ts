import { defineConfig } from "nitro/config";

const apiOrigin = process.env["API_ORIGIN"]?.replace(/\/$/, "");
if (process.env["VERCEL"] && !apiOrigin) {
  throw new Error("Set API_ORIGIN to the HTTPS Render service origin before deploying.");
}
if (apiOrigin) {
  const url = new URL(apiOrigin);
  if (url.protocol !== "https:" || url.origin !== apiOrigin) {
    throw new Error("API_ORIGIN must be an HTTPS origin without credentials, path, or query.");
  }
}
if (process.env["VERCEL"] && process.env["VITE_API_BASE_URL"]) {
  throw new Error("Leave VITE_API_BASE_URL empty: production uses the same-origin /api proxy.");
}

export default defineConfig({
  // Nitro emits this as a Vercel CDN rewrite, before the SSR catch-all route.
  // Public league reads can be slightly stale while Render wakes up. All account,
  // moderation and mutation routes retain no-store through the fallback rule.
  routeRules: apiOrigin
    ? {
        "/api/**": {
          proxy: `${apiOrigin}/api/**`,
          headers: {
            "Cache-Control": "no-store",
            "x-vercel-enable-rewrite-caching": "0",
          },
        },
        "/api/matches": {
          proxy: `${apiOrigin}/api/matches`,
          headers: {
            "Cache-Control": "public, max-age=0, must-revalidate",
            "CDN-Cache-Control": "public, max-age=300, stale-while-revalidate=3600",
            "x-vercel-enable-rewrite-caching": "1",
          },
        },
        "/api/matches/**": {
          proxy: `${apiOrigin}/api/matches/**`,
          headers: {
            "Cache-Control": "public, max-age=0, must-revalidate",
            "CDN-Cache-Control": "public, max-age=300, stale-while-revalidate=3600",
            "x-vercel-enable-rewrite-caching": "1",
          },
        },
        "/api/standings": {
          proxy: `${apiOrigin}/api/standings`,
          headers: {
            "Cache-Control": "public, max-age=0, must-revalidate",
            "CDN-Cache-Control": "public, max-age=300, stale-while-revalidate=3600",
            "x-vercel-enable-rewrite-caching": "1",
          },
        },
      }
    : {},
});
