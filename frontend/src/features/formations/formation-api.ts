import { useQuery } from "@tanstack/react-query";

export type Placement = {
  player_id: string;
  placement: "pitch" | "bench";
  x: number | null;
  y: number | null;
};
export type BoardPlayer = {
  id: string;
  display_name: string;
  chinese_name: string | null;
  photo_url: string | null;
  has_uploaded_photo: boolean;
  shirt_number: number | null;
  description: string | null;
  position: string | null;
  goals: number;
  assists: number;
};
export type Formation = {
  match_id: string;
  status: string;
  kickoff_at: string | null;
  editable: boolean;
  placements: Placement[];
  players: BoardPlayer[];
};
const base = (import.meta.env?.["VITE_API_BASE_URL"] ?? "").replace(/\/$/, "");
export class FormationError extends Error {
  constructor(public status: number) {
    super(`Formation request failed: ${status}`);
  }
}
export async function formationRequest(
  id: string,
  placements?: Placement[],
  signal?: AbortSignal,
): Promise<Formation> {
  const response = await fetch(`${base}/api/formations/${encodeURIComponent(id)}`, {
    credentials: "include",
    cache: "no-store",
    ...(signal ? { signal } : {}),
    ...(placements
      ? {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ placements }),
        }
      : {}),
  });
  if (!response.ok) throw new FormationError(response.status);
  return response.json() as Promise<Formation>;
}
export function useFormation(id: string, viewer: string) {
  return useQuery({
    queryKey: ["formation", id, viewer],
    queryFn: ({ signal }) => formationRequest(id, undefined, signal),
    staleTime: 0,
    gcTime: 0,
    retry: false,
    refetchInterval: 30_000,
  });
}
