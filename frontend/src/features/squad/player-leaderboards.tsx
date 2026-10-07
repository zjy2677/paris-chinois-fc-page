import { Link } from "@tanstack/react-router";
import { useI18n } from "@/i18n/i18n-provider";
import { localizedPlayerName } from "@/lib/player-name";
import { playerPhotoUrl, usePlayerLeaderboards, type LeaderboardEntry } from "./squad-api";

function Leaderboard({
  title,
  entries,
  unit,
  compact,
}: {
  title: string;
  entries: LeaderboardEntry[];
  unit: string;
  compact: boolean;
}) {
  const { language, t } = useI18n();
  const visible = compact ? entries.slice(0, 1) : entries;
  return (
    <article className="border border-border bg-card">
      <div className="flex items-center justify-between border-b border-border px-5 py-4">
        <h3 className="font-display text-2xl font-bold uppercase md:text-3xl">{title}</h3>
        {!compact ? <span className="eyebrow text-copper">{t("leaderboards.rank")}</span> : null}
      </div>
      {visible.length === 0 ? (
        <p className="px-5 py-8 text-sm text-muted-foreground">{t("leaderboards.empty")}</p>
      ) : (
        <ol>
          {visible.map((entry) => {
            const name = localizedPlayerName(entry.display_name, entry.chinese_name, language);
            const photo = playerPhotoUrl({
              id: entry.player_id,
              photo_url: entry.photo_url,
              has_uploaded_photo: entry.has_uploaded_photo,
            });
            return (
              <li
                key={entry.player_id}
                className="grid grid-cols-[2.25rem_3rem_1fr_auto] items-center gap-3 border-b border-border px-5 py-3 last:border-b-0"
              >
                <span className="font-display text-2xl font-bold text-copper">{entry.rank}</span>
                <div className="flex h-12 w-12 items-center justify-center overflow-hidden rounded-full bg-secondary">
                  {photo ? (
                    <img src={photo} alt="" className="h-full w-full object-cover" loading="lazy" />
                  ) : (
                    <span className="font-display text-lg text-muted-foreground">
                      {entry.shirt_number ?? name.slice(0, 1)}
                    </span>
                  )}
                </div>
                <Link
                  to="/team/$playerId"
                  params={{ playerId: `player_${entry.player_id}` }}
                  className="min-w-0 truncate font-bold hover:text-copper"
                >
                  {name}
                </Link>
                <strong className="whitespace-nowrap font-display text-2xl">
                  {entry.total} <span className="text-sm text-muted-foreground">{unit}</span>
                </strong>
              </li>
            );
          })}
        </ol>
      )}
    </article>
  );
}

export function PlayerLeaderboards({ compact = false }: { compact?: boolean }) {
  const { t } = useI18n();
  const query = usePlayerLeaderboards();
  if (query.isPending) {
    return <p className="py-8 text-muted-foreground">{t("leaderboards.loading")}</p>;
  }
  if (query.isError || !query.data) {
    return <p className="py-8 text-copper">{t("leaderboards.error")}</p>;
  }
  return (
    <div className="grid gap-5 md:grid-cols-2">
      <Leaderboard
        title={t("leaderboards.scorers")}
        entries={query.data.scorers}
        unit={t("leaderboards.goals")}
        compact={compact}
      />
      <Leaderboard
        title={t("leaderboards.assists")}
        entries={query.data.assists}
        unit={t("leaderboards.assistUnit")}
        compact={compact}
      />
    </div>
  );
}
