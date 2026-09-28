import { useI18n } from "@/i18n/i18n-provider";
import { Link } from "@tanstack/react-router";
import { ArrowUpRight } from "lucide-react";
import { Hero } from "./hero";
import { MatchList } from "@/features/league/match-list";
import { LeagueTable } from "@/features/league/league-table";
import { assets } from "@/config/assets";
function SectionLink({ to, children }: { to: "/league" | "/about"; children: React.ReactNode }) {
  return (
    <Link
      to={to}
      className="inline-flex items-center gap-2 border-b border-copper pb-1 text-xs font-bold uppercase tracking-wider text-copper transition-colors hover:text-foreground"
    >
      {children}
      <ArrowUpRight size={16} />
    </Link>
  );
}
export function HomePage() {
  const { t } = useI18n();
  return (
    <>
      <Hero />
      <section className="border-b border-border bg-card">
        <div className="site-container grid lg:grid-cols-2">
          <div className="border-b border-border py-14 lg:border-b-0 lg:border-r lg:pr-12">
            <div className="flex items-end justify-between gap-3">
              <div>
                <p className="eyebrow text-primary">{t("01 / The next 90")}</p>
                <h2 className="mt-3 font-display text-5xl font-bold uppercase md:text-6xl">
                  {t("Next match")}
                </h2>
              </div>
              <SectionLink to="/league">{t("All fixtures")}</SectionLink>
            </div>
            <div className="mt-7">
              <MatchList compact />
            </div>
          </div>
          <div className="py-14 lg:pl-12">
            <div className="flex items-end justify-between gap-3">
              <div>
                <p className="eyebrow text-copper">{t("02 / Last whistle")}</p>
                <h2 className="mt-3 font-display text-5xl font-bold uppercase md:text-6xl">
                  {t("Latest result")}
                </h2>
              </div>
              <SectionLink to="/league">{t("Results")}</SectionLink>
            </div>
            <div className="mt-7">
              <MatchList results compact />
            </div>
          </div>
        </div>
      </section>
      <section className="site-container grid gap-12 py-20 lg:grid-cols-[.8fr_1.2fr] lg:gap-24 lg:py-28">
        <div>
          <p className="eyebrow text-primary">{t("03 / The standings")}</p>
          <h2 className="section-title mt-5">{t("The race is on.")}</h2>
          <p className="mt-7 max-w-sm leading-relaxed text-muted-foreground">
            {t(
              "Every point matters. Follow the club’s place in the FLA League as the season unfolds.",
            )}
          </p>
          <div className="mt-8">
            <SectionLink to="/league">{t("Full league table")}</SectionLink>
          </div>
        </div>
        <div className="min-w-0 self-center">
          <LeagueTable compact />
        </div>
      </section>
      <section className="relative min-h-[530px] overflow-hidden border-y border-border">
        <img
          src={assets.training}
          alt={t("Players training on a football pitch at dusk")}
          width={1280}
          height={896}
          loading="lazy"
          className="absolute inset-0 h-full w-full object-cover object-center"
        />
        <div className="absolute inset-0 bg-background/60" />
        <div className="site-container relative flex min-h-[530px] flex-col justify-end py-16">
          <p className="eyebrow text-copper">{t("More than a game")}</p>
          <h2 className="section-title mt-5 max-w-3xl">{t("A shared city. A shared passion.")}</h2>
          <p className="mt-6 max-w-xl text-foreground/85">
            {t("Built around a love of football and the connections it creates.")}
          </p>
          <div className="mt-7">
            <SectionLink to="/about">{t("Our story")}</SectionLink>
          </div>
        </div>
      </section>
    </>
  );
}
