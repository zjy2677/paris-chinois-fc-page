export type Team = { id: string; name: string; short: string; flaId?: number };
export type Match = {
  id: string;
  matchday: number | null;
  competitionKind?: "league" | "cup" | "custom";
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
  sourceType: "synced" | "manual";
};
export type MatchEvent = {
  id?: string;
  event_type: "goal" | "yellow_card" | "red_card";
  player_id: string | null;
  player_name?: string | null;
  assist_player_id: string | null;
  assist_player_name?: string | null;
  minute: number | null;
  sequence?: number;
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
  description: string | null;
  id: string;
  display_name: string;
  photo_url: string | null;
  has_uploaded_photo: boolean;
  shirt_number: number | null;
  season: string;
  active: boolean;
  position: "Goalkeepers" | "Defenders" | "Midfielders" | "Forwards";
  alternate_positions: Array<"Goalkeepers" | "Defenders" | "Midfielders" | "Forwards">;
};
