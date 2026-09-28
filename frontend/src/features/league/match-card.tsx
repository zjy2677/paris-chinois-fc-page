import { useI18n } from "@/i18n/i18n-provider";
import type { Match } from "@/types/football";

import { ArrowUpRight } from "lucide-react";
export function MatchCard({
  match,
  compact = false,
  showDetails = true,
}: {
  match: Match;
  compact?: boolean;
  showDetails?: boolean;
}) {
  const { t, formatDate } = useI18n();

  const date = match.date
    ? formatDate(match.date, {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric",
      })
    : t("league.tbc");
  const time = match.date
    ? formatDate(match.date, { hour: "2-digit", minute: "2-digit", hourCycle: "h23" })
    : "";
  return (
    <article className="border-t border-border py-7">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-2">
        <span className="eyebrow text-copper">
          {match.matchday !== null
            ? t("Matchday {number}", { number: match.matchday })
            : match.stage === "Phase de poules"
              ? t("league.groupStage")
              : match.stage}{" "}
          <span className="mx-2 text-muted-foreground">/</span>{" "}
          {match.competitionKind === "cup" ? match.competitionName : t("FLA League")}
        </span>
        <span
          className={`eyebrow ${match.status === "scheduled" ? "text-primary" : "text-muted-foreground"}`}
        >
          {t(`league.status.${match.status}`)}
        </span>
      </div>
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 sm:gap-6">
        <div className="min-w-0">
          <p className="font-display text-2xl font-bold uppercase leading-none sm:text-4xl">
            {match.home.name}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">{t("Home")}</p>
        </div>
        <div className="text-center font-display text-3xl font-bold tabular-nums text-copper sm:text-5xl">
          {match.score ? `${match.score[0]} : ${match.score[1]}` : t("VS")}
        </div>
        <div className="min-w-0 text-right">
          <p className="font-display text-2xl font-bold uppercase leading-none sm:text-4xl">
            {match.away.name}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">{t("Away")}</p>
        </div>
      </div>
      <div className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-muted-foreground">
        <span>
          {date}
          {time && (
            <>
              {" "}
              · {time} {t("Paris time")}
            </>
          )}
        </span>
        <span>
          {match.stadium || t("league.venueTbc")}
          {!compact && match.address && ` · ${match.address}`}
        </span>
        {showDetails && (
          <a
            href={`/matches/${encodeURIComponent(match.id)}`}
            className="inline-flex items-center gap-2 py-2 font-semibold text-copper underline-offset-4 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-copper"
          >
            {t("match.details")} <ArrowUpRight size={14} aria-hidden="true" />
          </a>
        )}
      </div>
    </article>
  );
}
