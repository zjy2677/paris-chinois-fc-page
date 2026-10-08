import { Link } from "@tanstack/react-router";
import { useI18n } from "@/i18n/i18n-provider";
import { localizedPlayerName } from "@/lib/player-name";
import { Button } from "@/components/ui/button";
import { PlayerCard } from "./player-card";
import { PlayerPortrait } from "./player-portrait";
import { PlayerApiError, playerPhotoUrl, usePlayerProfile } from "./squad-api";

export function PlayerProfilePage({ id }: { id: string }) {
  const { t, c, language } = useI18n();
  const query = usePlayerProfile(id);
  const missing = query.error instanceof PlayerApiError && [404, 422].includes(query.error.status);
  const player = query.data;
  const latest = player?.squads[0];
  return (
    <div className="site-container pb-12 pt-28 md:pb-20 md:pt-32">
      <Link to="/team" className="text-sm text-copper underline underline-offset-4">
        {t("profile.back")}
      </Link>
      {query.isPending ? (
        <p role="status" className="py-16">
          {t("squad.loading")}
        </p>
      ) : query.isError ? (
        <div role="alert" className="py-16">
          <h1 className="text-2xl">{t(missing ? "profile.notFound" : "squad.loadError")}</h1>
          {!missing && (
            <Button className="mt-4" onClick={() => query.refetch()}>
              {t("squad.retry")}
            </Button>
          )}
        </div>
      ) : player ? (
        <div className="mt-8 grid items-start gap-10 md:grid-cols-[minmax(0,1fr)_minmax(0,2fr)] md:gap-16">
          <div className="w-full max-w-sm">
            {latest ? (
              <PlayerCard player={{ ...player, ...latest }} showProfileLink={false} />
            ) : (
              <PlayerPortrait
                name={localizedPlayerName(player.display_name, player.chinese_name, language)}
                photoUrl={playerPhotoUrl(player)}
                number={null}
              />
            )}
          </div>
          <div className="min-w-0">
            <p className="eyebrow text-copper">{t("profile.label")}</p>
            <h1 className="mt-3 break-words font-display text-5xl font-bold leading-tight md:text-7xl">
              {localizedPlayerName(player.display_name, player.chinese_name, language)}
            </h1>
            {!player.active && <p className="mt-3 text-muted-foreground">{t("squad.inactive")}</p>}
            <section className="mt-8" aria-label={t("profile.description")}>
              <p className="whitespace-pre-line break-words leading-relaxed text-muted-foreground">
                {player.description || t("profile.noDescription")}
              </p>
            </section>
            <section className="mt-10" aria-labelledby="player-statistics">
              <h2 id="player-statistics" className="text-xl font-semibold">
                {t("profile.statistics")}
              </h2>
              <dl className="mt-5 grid grid-cols-2 gap-4">
                {(
                  [
                    ["profile.goals", player.goals],
                    ["profile.assists", player.assists],
                  ] as const
                ).map(([label, value]) => (
                  <div key={label} className="border-t-2 border-copper bg-card p-5 md:p-7">
                    <dt className="text-sm text-muted-foreground">{t(label)}</dt>
                    <dd className="mt-2 font-display text-5xl font-bold text-copper">{value}</dd>
                  </div>
                ))}
              </dl>
              <p className="mt-4 text-sm text-muted-foreground">{t("profile.statsHint")}</p>
            </section>
            <section className="mt-10" aria-labelledby="player-seasons">
              <h2 id="player-seasons" className="text-xl font-semibold">
                {t("profile.seasons")}
              </h2>
              {player.squads.length ? (
                <ul className="mt-4 divide-y divide-border">
                  {player.squads.map((squad) => (
                    <li key={squad.season} className="flex flex-wrap justify-between gap-3 py-4">
                      <span className="font-semibold">{squad.season}</span>
                      <span className="text-muted-foreground">
                        {c(squad.position.slice(0, -1))}
                        {(squad.alternate_positions ?? []).length > 0
                          ? ` · ${t("squad.alternateShort")}: ${(squad.alternate_positions ?? [])
                              .map((position) => c(position.slice(0, -1)))
                              .join(" / ")}`
                          : ""}
                        {squad.shirt_number !== null ? ` · #${squad.shirt_number}` : ""}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-4 text-muted-foreground">{t("profile.noSquad")}</p>
              )}
            </section>
          </div>
        </div>
      ) : null}
    </div>
  );
}
