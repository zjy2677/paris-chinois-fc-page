import { Link } from "@tanstack/react-router";
import { Play } from "lucide-react";
import { useI18n } from "@/i18n/i18n-provider";
import { PageIntro } from "@/components/layout/page-intro";
import { assets } from "@/config/assets";
import { useMatch, ApiError } from "./league-api";
import { DataState } from "./data-state";
import { MatchCard } from "./match-card";
import { HighlightPlayer } from "./highlight-player";

export function MatchDetailPage({ id }: { id: string }) {
  const { t } = useI18n();
  const query = useMatch(id);
  if (query.isPending || query.isError) {
    const missing = query.error instanceof ApiError && [404, 422].includes(query.error.status);
    return (
      <div className="site-container py-24">
        <Link to="/league">{t("match.back")}</Link>
        <DataState
          loading={query.isPending}
          error={query.isError && !missing}
          empty="Page not found"
          retry={() => void query.refetch()}
        />
      </div>
    );
  }
  const match = query.data;
  const videos = match.videos.filter((video) => video.embed_url);
  return (
    <>
      <PageIntro
        backgroundImage={assets.league}
        eyebrow={
          match.matchday !== null
            ? t("Matchday {number}", { number: match.matchday })
            : (match.competitionName ?? t("league.cup"))
        }
        title={`${match.home.name} — ${match.away.name}`}
      />
      <div className="site-container py-12 md:py-20">
        <Link to="/league" className="text-sm text-copper underline underline-offset-4">
          {t("match.back")}
        </Link>
        <div className="mt-8">
          <MatchCard match={match} showDetails={false} />
        </div>
        <section className="mt-10" aria-labelledby="match-highlights">
          <h2 id="match-highlights" className="font-display text-4xl font-bold uppercase">
            {t("match.highlights")}
          </h2>
          {videos.length > 0 ? (
            <div className="mt-6 space-y-8">
              {videos.map((video) => (
                <HighlightPlayer
                  key={video.id}
                  embedUrl={video.embed_url!}
                  title={video.title ?? t("match.highlights")}
                />
              ))}
            </div>
          ) : (
            <div className="mt-6 flex min-h-56 flex-col items-center justify-center gap-4 border border-border bg-card px-6 py-12 text-center md:min-h-72">
              <Play className="text-copper" size={32} aria-hidden="true" />
              <p className="max-w-lg text-muted-foreground">{t("match.noHighlights")}</p>
            </div>
          )}
        </section>
      </div>
    </>
  );
}
