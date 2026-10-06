import type { QueryClient, QueryKey } from "@tanstack/react-query";

const STORAGE_KEY = "pcfc-public-query-cache-v1";
const MAX_AGE = 24 * 60 * 60 * 1_000;
const MAX_QUERIES = 32;

type StoredQuery = {
  queryKey: QueryKey;
  data: unknown;
  updatedAt: number;
};

function isPublicQuery(queryKey: QueryKey) {
  return (
    (queryKey[0] === "league" &&
      (queryKey[1] === "matches" ||
        queryKey[1] === "standings" ||
        (queryKey[1] === "match" && typeof queryKey[2] === "string"))) ||
    (queryKey[0] === "players" && queryKey[1] === "leaderboards")
  );
}

export function restorePublicQueryCache(queryClient: QueryClient) {
  if (typeof window === "undefined") return;

  try {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (!saved) return;
    const queries = JSON.parse(saved) as StoredQuery[];
    const now = Date.now();

    for (const query of queries) {
      if (
        !Array.isArray(query.queryKey) ||
        !isPublicQuery(query.queryKey) ||
        typeof query.updatedAt !== "number" ||
        now - query.updatedAt > MAX_AGE
      ) {
        continue;
      }
      queryClient.setQueryData(query.queryKey, query.data, { updatedAt: query.updatedAt });
    }
  } catch {
    window.localStorage.removeItem(STORAGE_KEY);
  }
}

export function persistPublicQueries(queryClient: QueryClient) {
  if (typeof window === "undefined") return () => {};

  return queryClient.getQueryCache().subscribe((event) => {
    if (event.type !== "updated" || event.query.state.status !== "success") return;
    if (!isPublicQuery(event.query.queryKey)) return;

    try {
      const queries = queryClient
        .getQueryCache()
        .getAll()
        .filter(
          (query) =>
            isPublicQuery(query.queryKey) &&
            query.state.status === "success" &&
            Date.now() - query.state.dataUpdatedAt <= MAX_AGE,
        )
        .sort((a, b) => b.state.dataUpdatedAt - a.state.dataUpdatedAt)
        .slice(0, MAX_QUERIES)
        .map((query): StoredQuery => ({
          queryKey: query.queryKey,
          data: query.state.data,
          updatedAt: query.state.dataUpdatedAt,
        }));

      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(queries));
    } catch {
      // Storage may be disabled or full. Live API data continues to work normally.
    }
  });
}
