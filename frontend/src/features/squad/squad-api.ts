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
  constructor(public status: number) {
    super(`Player request failed: ${status}`);
  }
}
export type PlayerInput = Pick<Player, "display_name" | "photo_url" | "shirt_number" | "position">;
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
export function savePlayer(body: PlayerInput, id?: string) {
  return id
    ? playerRequest<Player>(
        `/players/${id}?season=${encodeURIComponent(SQUAD_SEASON)}`,
        "PATCH",
        body,
      )
    : playerRequest<Player>("/players", "POST", { ...body, season: SQUAD_SEASON });
}
