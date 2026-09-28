export type Team = { id: string; name: string; short: string; flaId?: number };
export type Match = {
  id: string;
  matchday: number | null;
  competitionKind?: "league" | "cup";
  competitionName?: string;
  stage?: string;
  competitionId?: string;
  date: string | null;
  home: Team;
  away: Team;
  stadium: string;
  address: string;
  status: "scheduled" | "final" | "postponed" | "cancelled" | "unknown";
  score?: [number, number] | undefined;
};
export type Standing = {
  position: number;
  team: Team;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  gd: number;
  points: number;
};
export type Player = {
  id: string;
  name: string;
  number: number;
  position: "Goalkeepers" | "Defenders" | "Midfielders" | "Forwards";
};
