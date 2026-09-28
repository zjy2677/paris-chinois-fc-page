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
  // Keep authentication cookies first-party; never cache authenticated responses.
  routeRules: apiOrigin
    ? { "/api/**": { proxy: `${apiOrigin}/api/**`, headers: { "Cache-Control": "no-store" } } }
    : {},
});
