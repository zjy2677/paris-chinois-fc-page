import { Link } from "@tanstack/react-router";
import { useI18n } from "@/i18n/i18n-provider";
import { localizedPlayerName } from "@/lib/player-name";
import { PlayerPortrait } from "@/features/squad/player-portrait";
import { playerPhotoUrl } from "@/features/squad/squad-api";
import { useMatchRatings } from "./ratings-api";
import { StarRating } from "./star-rating";

export function MatchRatingsSection({ matchId, final }: { matchId: string; final: boolean }) {
  const { t, language } = useI18n();
  const query = useMatchRatings(matchId, final);
  if (!final) return null;
  return (
    <section className="mt-14" aria-labelledby="match-player-ratings">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <h2 id="match-player-ratings" className="font-display text-4xl font-bold uppercase">
          {t("ratings.title")}
        </h2>
        <p className="text-sm text-muted-foreground">{t("ratings.hint")}</p>
      </div>
      {query.isPending ? (
        <p className="text-muted-foreground">{t("ratings.loading")}</p>
      ) : query.isError ? (
        <p role="alert" className="text-copper">
          {t("ratings.loadError")}
        </p>
      ) : query.data.length === 0 ? (
        <p className="border border-border bg-card p-6 text-muted-foreground">
          {t("ratings.noSquad")}
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {query.data.map((player) => {
            const name = localizedPlayerName(player.display_name, player.chinese_name, language);
            return (
              <Link
                key={player.player_id}
                to="/matches/$id/players/$playerId"
                params={{ id: matchId, playerId: player.player_id }}
                className="group flex min-w-0 items-center gap-4 border border-border bg-card p-3 transition hover:border-copper focus-visible:outline focus-visible:outline-2 focus-visible:outline-copper"
              >
                <div className="w-20 shrink-0 overflow-hidden rounded sm:w-24">
                  <PlayerPortrait
                    compact
                    name={name}
                    photoUrl={playerPhotoUrl({ ...player, id: player.player_id })}
                    number={player.shirt_number}
                  />
                </div>
                <div className="min-w-0">
                  <h3 className="truncate font-display text-xl font-bold group-hover:text-copper">
                    {name}
                  </h3>
                  <p className="mt-1 text-xs font-bold uppercase tracking-wide text-copper">
                    {t(`ratings.${player.participation}`)}
                  </p>
                  <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1">
                    <StarRating
                      value={player.average_stars}
                      label={
                        player.average_stars === null
                          ? t("ratings.unrated")
                          : t("ratings.starLabel", { score: player.average_stars })
                      }
                    />
                    <span className="font-bold tabular-nums">
                      {player.average_stars === null ? "—" : player.average_stars.toFixed(1)}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {t(player.rating_count === 1 ? "ratings.countOne" : "ratings.count", {
                      count: player.rating_count,
                    })}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </section>
  );
}
