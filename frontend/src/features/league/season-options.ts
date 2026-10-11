import type { CompetitionSeason } from "./league-api";

export type SeasonOption = {
  label: string;
  competitionIds: ReadonlySet<string>;
  leagueId: string | null;
};

export function seasonOptions(seasons: CompetitionSeason[]): SeasonOption[] {
  const byLabel = new Map<string, { ids: Set<string>; leagueId: string | null }>();
  for (const season of seasons) {
    const group = byLabel.get(season.season_label) ?? { ids: new Set(), leagueId: null };
    group.ids.add(season.id);
    if (season.competition_kind === "league") group.leagueId = season.id;
    byLabel.set(season.season_label, group);
  }
  return [...byLabel.entries()]
    .sort(([a], [b]) => b.localeCompare(a))
    .map(([label, group]) => ({
      label,
      competitionIds: group.ids,
      leagueId: group.leagueId,
    }));
}
