import { useI18n } from "@/i18n/i18n-provider";
import { useCompetitionSeasons, useStandings } from "./league-api";
import { DataState } from "./data-state";
import { seasonOptions } from "./season-options";
export function LeagueTable({
  compact = false,
  competitionSeasonId,
}: {
  compact?: boolean;
  competitionSeasonId?: string | null;
}) {
  const { t, c, formatDate } = useI18n();
  const seasons = useCompetitionSeasons();
  const newestLeagueId = seasonOptions(seasons.data ?? []).find(
    (option) => option.leagueId,
  )?.leagueId;
  const selectedId =
    competitionSeasonId === undefined ? (newestLeagueId ?? null) : competitionSeasonId;
  const query = useStandings(selectedId);
  if (competitionSeasonId === undefined && seasons.isPending) return <DataState loading />;
  if (competitionSeasonId === undefined && seasons.isError && !seasons.data)
    return <DataState error retry={() => void seasons.refetch()} />;
  if (selectedId === null) return <DataState />;
  if (query.isPending || query.isError)
    return (
      <DataState
        loading={query.isPending}
        error={query.isError}
        retry={() => void query.refetch()}
      />
    );
  if (!query.data.rows.length) return <DataState />;
  const standings = query.data.rows;
  // Keep the club in the homepage snapshot while retaining official ranks.
  const clubIndex = standings.findIndex((row) => row.team.flaId === 322);
  const start = compact ? Math.max(0, Math.min(clubIndex - 2, standings.length - 5)) : 0;
  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full min-w-[560px] border-collapse text-left text-sm tabular-nums">
        <caption className="sr-only">{t("League table")}</caption>
        <thead>
          <tr className="border-y border-border text-[10px] uppercase tracking-widest text-muted-foreground">
            <th scope="col" className="py-4 pl-3 font-medium">
              {t("Pos")}
            </th>
            <th scope="col" className="py-4 font-medium">
              {t("Team")}
            </th>
            {["P", "W", "D", "L", "GD", "Pts"].map((x) => (
              <th scope="col" key={x} className="px-2 py-4 text-center font-medium">
                {c(x)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {standings.slice(start, compact ? start + 5 : undefined).map((row) => (
            <tr
              key={row.team.id}
              className={`border-b border-border ${row.team.flaId === 322 ? "bg-oxblood/35 text-foreground" : "text-muted-foreground"}`}
            >
              <td className="py-4 pl-3 font-display text-xl font-bold text-copper">
                {String(row.position).padStart(2, "0")}
              </td>
              <th scope="row" className="min-w-36 py-4 font-semibold text-foreground">
                {row.team.name}
              </th>
              <td className="px-2 text-center">{row.played}</td>
              <td className="px-2 text-center">{row.won}</td>
              <td className="px-2 text-center">{row.drawn}</td>
              <td className="px-2 text-center">{row.lost}</td>
              <td className="px-2 text-center">
                {row.gd > 0 ? "+" : ""}
                {row.gd}
              </td>
              <td className="px-2 text-center font-bold text-foreground">{row.points}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {query.data.source && (
        <p className="mt-4 text-xs text-muted-foreground">
          <a href={query.data.source} target="_blank" rel="noreferrer" className="underline">
            {t("league.source")}
          </a>
          {query.data.syncedAt && (
            <>
              {" "}
              · {t("league.updated")}{" "}
              {formatDate(query.data.syncedAt, { dateStyle: "short", timeStyle: "short" })}
            </>
          )}
        </p>
      )}
    </div>
  );
}
