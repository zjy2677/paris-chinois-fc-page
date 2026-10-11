import { useState } from "react";
import { assets } from "@/config/assets";
import { useI18n } from "@/i18n/i18n-provider";
import { PageIntro } from "@/components/layout/page-intro";
import { MatchList } from "./match-list";
import { LeagueTable } from "./league-table";
import { DataState } from "./data-state";
import { useCompetitionSeasons } from "./league-api";
import { seasonOptions } from "./season-options";
import { useAccount } from "@/features/auth/auth-api";
import { CreateMatchForm } from "./create-match-form";
export function LeaguePage() {
  const { t } = useI18n();
  const account = useAccount();
  const seasons = useCompetitionSeasons();
  const [selectedLabel, setSelectedLabel] = useState<string | null>(null);
  const options = seasonOptions(seasons.data ?? []);
  const selected = options.find((option) => option.label === selectedLabel) ?? options[0];
  return (
    <>
      <PageIntro
        backgroundImage={assets.league}
        {...(selected ? { eyebrow: t("league.season", { season: selected.label }) } : {})}
        title={t("FLA League")}
      />
      <div className="site-container py-16 md:py-24">
        {seasons.isPending ? (
          <DataState loading />
        ) : seasons.isError ? (
          <DataState error retry={() => void seasons.refetch()} />
        ) : !selected ? (
          <DataState empty="league.noSeasons" />
        ) : (
          <>
            <div className="mb-10 flex flex-wrap items-center gap-3">
              <label htmlFor="league-season" className="font-semibold">
                {t("league.selectSeason")}
              </label>
              <select
                id="league-season"
                value={selected.label}
                onChange={(event) => setSelectedLabel(event.target.value)}
                className="min-h-11 w-full border border-border bg-card px-4 py-2 text-foreground focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-copper sm:w-auto"
              >
                {options.map((option) => (
                  <option key={option.label} value={option.label}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            {account.data?.role === "admin" && (
              <div className="mb-12">
                <CreateMatchForm />
              </div>
            )}
            <div className="grid gap-14 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
              <section>
                <p className="eyebrow mb-3 text-primary">{t("Coming up")}</p>
                <h2 className="font-display text-5xl font-bold uppercase md:text-6xl">
                  {t("Upcoming games")}
                </h2>
                <div className="mt-8">
                  <MatchList
                    key={`upcoming-${selected.label}`}
                    seasonIds={selected.competitionIds}
                  />
                </div>
              </section>
              <section>
                <p className="eyebrow mb-3 text-copper">{t("From the pitch")}</p>
                <h2 className="font-display text-5xl font-bold uppercase md:text-6xl">
                  {t("Recent results")}
                </h2>
                <div className="mt-8">
                  <MatchList
                    key={`results-${selected.label}`}
                    results
                    seasonIds={selected.competitionIds}
                  />
                </div>
              </section>
            </div>
            <section className="mt-20">
              <p className="eyebrow mb-3 text-primary">{t("The race")}</p>
              <h2 className="font-display text-5xl font-bold uppercase md:text-6xl">
                {t("League table")}
              </h2>
              <div className="mt-8">
                <LeagueTable competitionSeasonId={selected.leagueId} />
              </div>
            </section>
          </>
        )}
      </div>
    </>
  );
}
