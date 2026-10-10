import { useQuery } from "@tanstack/react-query";

export type PlayerRatingSummary = {
  player_id: string;
  display_name: string;
  chinese_name: string | null;
  photo_url: string | null;
  has_uploaded_photo: boolean;
  shirt_number: number | null;
  participation: "start" | "sub" | "absent";
  average_stars: number | null;
  rating_count: number;
};
export type RatingItem = {
  id: string;
  stars: number;
  comment: string | null;
  author_name: string;
  created_at: string;
  updated_at: string;
};
export type PlayerRatingDetail = {
  summary: PlayerRatingSummary;
  ratings: RatingItem[];
};
export type MyRating = { stars: number; comment: string | null };

const base = (import.meta.env?.["VITE_API_BASE_URL"] ?? "").replace(/\/$/, "");
export class RatingError extends Error {
  constructor(public status: number) {
    super(`Rating request failed: ${status}`);
  }
}
const path = (matchId: string, playerId: string) =>
  `${base}/api/matches/${encodeURIComponent(matchId)}/players/${encodeURIComponent(playerId)}`;
async function json<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, {
    credentials: "include",
    cache: "no-store",
    ...(signal ? { signal } : {}),
  });
  if (!response.ok) throw new RatingError(response.status);
  return response.json() as Promise<T>;
}
export function useMatchRatings(matchId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["ratings", matchId],
    enabled: enabled && typeof window !== "undefined",
    queryFn: ({ signal }) =>
      json<PlayerRatingSummary[]>(
        `${base}/api/matches/${encodeURIComponent(matchId)}/ratings`,
        signal,
      ),
  });
}
export function usePlayerRatings(matchId: string, playerId: string) {
  return useQuery({
    queryKey: ["ratings", matchId, playerId],
    enabled: typeof window !== "undefined",
    queryFn: ({ signal }) => json<PlayerRatingDetail>(`${path(matchId, playerId)}/ratings`, signal),
  });
}
export function useMyRating(matchId: string, playerId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["ratings", matchId, playerId, "mine"],
    enabled: enabled && typeof window !== "undefined",
    queryFn: ({ signal }) =>
      json<MyRating | null>(`${path(matchId, playerId)}/rating/mine`, signal),
  });
}
export async function saveRating(matchId: string, playerId: string, rating: MyRating) {
  const response = await fetch(`${path(matchId, playerId)}/rating`, {
    method: "PUT",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(rating),
  });
  if (!response.ok) throw new RatingError(response.status);
}
export async function deleteRating(matchId: string, playerId: string) {
  const response = await fetch(`${path(matchId, playerId)}/rating`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!response.ok) throw new RatingError(response.status);
}
