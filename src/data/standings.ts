import type { Standing } from '@/types/football';
import { teams } from './teams';
// Illustrative league-wide table: every club has played four matches; totals balance across the league.
export const standings: Standing[] = [
  { team: teams.paris, played: 4, won: 3, drawn: 1, lost: 0, gd: 5, points: 10 },
  { team: teams.belleville, played: 4, won: 3, drawn: 0, lost: 1, gd: 4, points: 9 },
  { team: teams.atlas, played: 4, won: 2, drawn: 1, lost: 1, gd: 2, points: 7 },
  { team: teams.seine, played: 4, won: 1, drawn: 1, lost: 2, gd: -1, points: 4 },
  { team: teams.bastille, played: 4, won: 1, drawn: 0, lost: 3, gd: -4, points: 3 },
  { team: teams.montmartre, played: 4, won: 0, drawn: 1, lost: 3, gd: -6, points: 1 },
];
