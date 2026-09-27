export type Team = { id: string; name: string; short: string };
export type Match = { id: string; matchday: number; date: string; home: Team; away: Team; stadium: string; address: string; status: 'scheduled' | 'final'; score?: [number, number] };
export type Standing = { team: Team; played: number; won: number; drawn: number; lost: number; gd: number; points: number };
export type Player = { id: string; name: string; number: number; position: 'Goalkeepers' | 'Defenders' | 'Midfielders' | 'Forwards' };
