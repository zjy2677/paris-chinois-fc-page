import { assets } from "@/config/assets";
import { useI18n } from "@/i18n/i18n-provider";
import { PageIntro } from "@/components/layout/page-intro";
import { MatchList } from "./match-list";
import { LeagueTable } from "./league-table";
export function LeaguePage() {
  const { t } = useI18n();
  return (
    <>
      <PageIntro
        backgroundImage={assets.league}
        eyebrow={t("Season 2026 / 27")}
        title={t("FLA League")}
      />
      <div className="site-container py-16 md:py-24">
        <div className="grid gap-14 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
          <section>
            <p className="eyebrow mb-3 text-primary">{t("Coming up")}</p>
            <h2 className="font-display text-5xl font-bold uppercase md:text-6xl">
              {t("Upcoming games")}
            </h2>
            <div className="mt-8">
              <MatchList />
            </div>
          </section>
          <section>
            <p className="eyebrow mb-3 text-copper">{t("From the pitch")}</p>
            <h2 className="font-display text-5xl font-bold uppercase md:text-6xl">
              {t("Recent results")}
            </h2>
            <div className="mt-8">
              <MatchList results />
            </div>
          </section>
        </div>
        <section className="mt-20">
          <p className="eyebrow mb-3 text-primary">{t("The race")}</p>
          <h2 className="font-display text-5xl font-bold uppercase md:text-6xl">
            {t("League table")}
          </h2>
          <div className="mt-8">
            <LeagueTable />
          </div>
        </section>
      </div>
    </>
  );
}
