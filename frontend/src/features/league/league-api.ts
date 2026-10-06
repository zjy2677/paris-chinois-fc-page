import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Match, MatchEvent, Player, Standing, Team } from "@/types/football";

const base = (import.meta.env?.["VITE_API_BASE_URL"] ?? "").replace(/\/$/, "");
export class ApiError extends Error {
  constructor(public status: number) {
    super(`API request failed: ${status}`);
  }
}
async function get<T>(path: string, signal: AbortSignal): Promise<T> {
  const response = await fetch(`${base}/api${path}`, { signal });
  if (!response.ok) throw new ApiError(response.status);
  return response.json() as Promise<T>;
}
type ApiTeam = { id: string; fla_team_id: number | null; name: string; logo_url: string | null };
type ApiMatch = {
  id: string;
  competition_season_id: string;
  home_team: ApiTeam;
  away_team: ApiTeam;
  venue: { name: string; address: string } | null;
  kickoff_at: string | null;
  matchday: number | null;
  competition_kind: "league" | "cup" | "custom";
  competition_name: string;
  leg: string;
  status: Match["status"];
  home_score: number | null;
  away_score: number | null;
  source_url: string;
  last_synced_at: string;
  source_type: "synced" | "manual";
};
type ApiStanding = {
  team: ApiTeam;
  position: number;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goal_difference: number;
  points: number;
};
const team = (t: ApiTeam): Team => ({
  id: t.id,
  name: t.name,
  short: t.name,
  ...(t.fla_team_id !== null ? { flaId: t.fla_team_id } : {}),
});
export const toMatch = (m: ApiMatch): Match => ({
  id: m.id,
  competitionId: m.competition_season_id,
  matchday: m.matchday,
  competitionKind: m.competition_kind,
  competitionName: m.competition_name,
  stage: m.leg,
  date: m.kickoff_at,
  home: team(m.home_team),
  away: team(m.away_team),
  stadium: m.venue?.name ?? "",
  address: m.venue?.address ?? "",
  status: m.status,
  score: m.home_score !== null && m.away_score !== null ? [m.home_score, m.away_score] : undefined,
  sourceType: m.source_type,
});
export function useMatches() {
  return useQuery({
    queryKey: ["league", "matches"],
    enabled: typeof window !== "undefined",
    staleTime: 60_000,
    retry: 1,
    queryFn: async ({ signal }) => {
      const items: ApiMatch[] = [];
      let total: number;
      do {
        const page = await get<{ items: ApiMatch[]; total: number }>(
          `/matches?limit=100&offset=${items.length}`,
          signal,
        );
        total = page.total;
        if (!page.items.length) break;
        items.push(...page.items);
      } while (items.length < total);
      return items
        .filter((m) => m.home_team.fla_team_id === 322 || m.away_team.fla_team_id === 322)
        .map(toMatch);
    },
  });
}
export function useStandings() {
  return useQuery({
    queryKey: ["league", "standings"],
    enabled: typeof window !== "undefined",
    staleTime: 60_000,
    retry: 1,
    queryFn: async ({ signal }) => {
      const result = await get<{
        rows: ApiStanding[];
        source_url: string | null;
        last_successful_sync: string | null;
      }>("/standings", signal);
      return {
        source: result.source_url,
        syncedAt: result.last_successful_sync,
        rows: result.rows.map((r): Standing => ({
          team: team(r.team),
          position: r.position,
          played: r.played,
          won: r.wins,
          drawn: r.draws,
          lost: r.losses,
          gd: r.goal_difference,
          points: r.points,
        })),
      };
    },
  });
}
export type Highlight = { id: string; title: string | null; embed_url: string | null };
export type MatchDetail = Match & {
  videos: Highlight[];
  description: string | null;
  events: MatchEvent[];
};
type ApiMatchDetail = ApiMatch & {
  videos: Highlight[];
  description: string | null;
  events: MatchEvent[];
};
const toMatchDetail = (data: ApiMatchDetail): MatchDetail => ({
  ...toMatch(data),
  videos: data.videos,
  description: data.description,
  events: data.events,
});
export function useMatch(id: string) {
  return useQuery({
    queryKey: ["league", "match", id],
    refetchOnMount: "always",
    enabled: typeof window !== "undefined",
    staleTime: 60_000,
    retry: (count, error) =>
      !(error instanceof ApiError && [404, 422].includes(error.status)) && count < 1,
    queryFn: async ({ signal }) => {
      const data = await get<ApiMatchDetail>(`/matches/${encodeURIComponent(id)}`, signal);
      return toMatchDetail(data);
    },
  });
}

export function usePlayers() {
  return useQuery({
    queryKey: ["players", "2026/2027"],
    queryFn: ({ signal }) =>
      get<
        Array<{
          id: string;
          display_name: string;
          chinese_name: string | null;
          shirt_number: number | null;
          position: Player["position"];
        }>
      >("/players", signal),
    select: (rows) =>
      rows.map((p) => ({
        id: p.id,
        name: p.display_name,
        chineseName: p.chinese_name,
        number: p.shirt_number ?? 0,
        position: p.position,
      })),
  });
}

async function adminRequest<T>(
  path: string,
  method: "DELETE" | "POST" | "PUT",
  body?: unknown,
): Promise<T> {
  const response = await fetch(`${base}/api/admin${path}`, {
    method,
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  if (!response.ok) throw new ApiError(response.status);
  return response.json() as Promise<T>;
}

export function useAddMatchVideo(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { url: string; title: string | null }) =>
      adminRequest<ApiMatchDetail>(`/matches/${encodeURIComponent(id)}/videos`, "POST", body).then(
        toMatchDetail,
      ),
    onSuccess: (data) => queryClient.setQueryData(["league", "match", id], data),
  });
}

export function useDeleteMatchVideo(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (videoId: string) =>
      adminRequest<ApiMatchDetail>(
        `/matches/${encodeURIComponent(id)}/videos/${encodeURIComponent(videoId)}`,
        "DELETE",
      ).then(toMatchDetail),
    onSuccess: (data) => queryClient.setQueryData(["league", "match", id], data),
  });
}

export function useSaveMatchRecord(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      description: string | null;
      home_score: number | null;
      away_score: number | null;
      events: Omit<
        MatchEvent,
        | "id"
        | "player_name"
        | "player_chinese_name"
        | "assist_player_name"
        | "assist_player_chinese_name"
        | "sequence"
      >[];
    }) =>
      adminRequest<ApiMatchDetail>(`/matches/${encodeURIComponent(id)}/record`, "PUT", body).then(
        toMatchDetail,
      ),
    onSuccess: (data) => {
      queryClient.setQueryData(["league", "match", id], data);
      void queryClient.invalidateQueries({ queryKey: ["league", "matches"] });
    },
  });
}

export function useCreateMatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      adminRequest<ApiMatchDetail>("/matches", "POST", body).then(toMatchDetail),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["league", "matches"] }),
  });
}
