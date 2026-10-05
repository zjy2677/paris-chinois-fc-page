import { useQuery } from "@tanstack/react-query";
import type { Player } from "@/types/football";

export const positions: Player["position"][] = [
  "Goalkeepers",
  "Defenders",
  "Midfielders",
  "Forwards",
];
export const SQUAD_SEASON = "2026/2027";
const base = (import.meta.env?.["VITE_API_BASE_URL"] ?? "").replace(/\/$/, "");
export class PlayerApiError extends Error {
  /** Create a player API error retaining the failed HTTP status. */
  constructor(public status: number) {
    super(`Player request failed: ${status}`);
  }
}
export type PlayerInput = Pick<
  Player,
  "display_name" | "shirt_number" | "position" | "alternate_positions" | "description"
> & { photo_url?: string | null };
export type PlayerProfile = Pick<
  Player,
  "id" | "display_name" | "photo_url" | "has_uploaded_photo" | "description" | "active"
> & {
  squads: Pick<Player, "season" | "position" | "alternate_positions" | "shirt_number">[];
  goals: number;
  assists: number;
};

export function usePlayerProfile(id: string) {
  return useQuery({
    queryKey: ["players", "profile", id],
    enabled: typeof window !== "undefined",
    queryFn: ({ signal }) =>
      playerRequest<PlayerProfile>(`/players/${encodeURIComponent(id)}`, "GET", undefined, signal),
    retry: (count, error) =>
      !(error instanceof PlayerApiError && [404, 422].includes(error.status)) && count < 1,
  });
}
/** Send a credentialed player API request; return JSON or undefined for 204, and throw on HTTP errors. */
export async function playerRequest<T>(
  path: string,
  method = "GET",
  body?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(`${base}/api${path}`, {
    method,
    credentials: "include",
    ...(signal ? { signal } : {}),
    ...(body !== undefined
      ? { headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
      : {}),
  });
  if (!response.ok) throw new PlayerApiError(response.status);
  return response.status === 204 ? (undefined as T) : (response.json() as Promise<T>);
}
/** Query the current season squad, using separate public and per-admin caches for inactive-player access. */
export function useSquad(adminId?: string) {
  return useQuery({
    queryKey: ["players", SQUAD_SEASON, adminId ?? "public"],
    enabled: typeof window !== "undefined",
    queryFn: ({ signal }) =>
      playerRequest<Player[]>(
        `${adminId ? "/admin" : ""}/players?season=${encodeURIComponent(SQUAD_SEASON)}`,
        "GET",
        undefined,
        signal,
      ),
    retry: 1,
  });
}
/** Create a player in the current season, or update that season membership and player details by ID. */
export function savePlayer(body: PlayerInput, id?: string) {
  return id
    ? playerRequest<Player>(
        `/players/${id}?season=${encodeURIComponent(SQUAD_SEASON)}`,
        "PATCH",
        body,
      )
    : playerRequest<Player>("/players", "POST", { ...body, season: SQUAD_SEASON });
}

export async function uploadPlayerPhoto(id: string, file: File): Promise<void> {
  const response = await fetch(`${base}/api/players/${encodeURIComponent(id)}/photo`, {
    method: "PUT",
    credentials: "include",
    headers: { "Content-Type": file.type },
    body: file,
  });
  if (!response.ok) throw new PlayerApiError(response.status);
}

export function playerPhotoUrl(player: Pick<Player, "id" | "photo_url" | "has_uploaded_photo">) {
  return player.has_uploaded_photo
    ? `${base}/api/players/${encodeURIComponent(player.id)}/photo`
    : player.photo_url;
}
