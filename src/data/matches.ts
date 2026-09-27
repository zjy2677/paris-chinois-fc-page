import type { Match } from '@/types/football';
import { teams } from './teams';
export const matches: Match[] = [
  { id: 'm5', matchday: 5, date: '2026-10-16T20:30:00+02:00', home: teams.paris, away: teams.atlas, stadium: 'Stade de la Porte de Choisy', address: 'Paris 13e, France', status: 'scheduled' },
  { id: 'm6', matchday: 6, date: '2026-10-24T18:00:00+02:00', home: teams.belleville, away: teams.paris, stadium: 'Stade de Belleville', address: 'Paris 20e, France', status: 'scheduled' },
  { id: 'm7', matchday: 7, date: '2026-10-31T19:00:00+01:00', home: teams.paris, away: teams.montmartre, stadium: 'Stade de la Porte de Choisy', address: 'Paris 13e, France', status: 'scheduled' },
  { id: 'm4', matchday: 4, date: '2026-10-09T20:30:00+02:00', home: teams.seine, away: teams.paris, stadium: 'Stade de la Seine', address: 'Paris, France', status: 'final', score: [1, 2] },
  { id: 'm3', matchday: 3, date: '2026-10-02T20:30:00+02:00', home: teams.paris, away: teams.bastille, stadium: 'Stade de la Porte de Choisy', address: 'Paris 13e, France', status: 'final', score: [3, 0] },
  { id: 'm2', matchday: 2, date: '2026-09-25T20:30:00+02:00', home: teams.atlas, away: teams.paris, stadium: 'Paris, France', address: 'Paris, France', status: 'final', score: [2, 2] },
  { id: 'm1', matchday: 1, date: '2026-09-18T20:30:00+02:00', home: teams.paris, away: teams.montmartre, stadium: 'Stade de la Porte de Choisy', address: 'Paris 13e, France', status: 'final', score: [1, 0] },
];
export const nextMatch = matches[0];
export const latestResult = matches[3];
export function formatMatchDate(date: string, options: Intl.DateTimeFormatOptions) {
  const parts = new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Paris', ...options }).formatToParts(new Date(date));
  const get = (type: string) => parts.find(part => part.type === type)?.value ?? '';
  if (options.hour) return `${get('hour')}:${get('minute')}`;
  return `${get('weekday')} ${get('day')} ${get('month')} ${get('year')}`.trim();
}
