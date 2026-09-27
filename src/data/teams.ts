import type { Team } from '@/types/football';
export const teams: Record<string, Team> = {
  paris: { id: 'paris', name: 'Paris Chinois FC', short: 'PCFC' },
  atlas: { id: 'atlas', name: 'Atlas Paris', short: 'ATLAS' },
  belleville: { id: 'belleville', name: 'Belleville United', short: 'BEL' },
  seine: { id: 'seine', name: 'Seine Athletic', short: 'SEINE' },
  bastille: { id: 'bastille', name: 'Bastille FC', short: 'BAS' },
  montmartre: { id: 'montmartre', name: 'Montmartre SC', short: 'MON' },
};
