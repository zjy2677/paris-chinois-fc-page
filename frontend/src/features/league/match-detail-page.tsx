import { TacticalBoard } from "@/features/formations/tactical-board";
import { Link } from "@tanstack/react-router";
import { Play } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useI18n } from "@/i18n/i18n-provider";
import { localizedPlayerName } from "@/lib/player-name";
import { PageIntro } from "@/components/layout/page-intro";
import { assets } from "@/config/assets";
import { useMatch, ApiError } from "./league-api";
import { DataState } from "./data-state";
import { MatchCard } from "./match-card";
import { HighlightPlayer } from "./highlight-player";
import { useAccount } from "@/features/auth/auth-api";
import { MatchRecordEditor } from "./match-record-editor";
import { HighlightEditor } from "./highlight-editor";
import { PhotoGrid } from "@/features/gallery/photo-grid";
import { PhotoUploadError, uploadPhotos } from "@/features/gallery/upload-photos";
import { MatchRatingsSection } from "@/features/ratings/match-ratings-section";

export function MatchDetailPage({ id }: { id: string }) {
  const { t, language } = useI18n();
  const query = useMatch(id);
  const account = useAccount();
  const [hydrated, setHydrated] = useState(false);
  // Cached client queries must not replace the server loading view during hydration.
  useEffect(() => setHydrated(true), []);
  const [photoFiles, setPhotoFiles] = useState<File[]>([]);
  const [photoPending, setPhotoPending] = useState(false);
  const [photoError, setPhotoError] = useState<string | null>(null);
  const photoInput = useRef<HTMLInputElement>(null);
  const uploading = useRef(false);
  if (!hydrated || query.isPending || query.isError) {
    const missing = query.error instanceof ApiError && [404, 422].includes(query.error.status);
    return (
      <div className="site-container py-24">
        <Link to="/league">{t("match.back")}</Link>
        <DataState
          loading={!hydrated || query.isPending}
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
        <TacticalBoard match={match} />
        {account.data?.role === "admin" && <MatchRecordEditor match={match} />}
        {match.events.length > 0 && (
          <section className="mt-10" aria-labelledby="match-events">
            <h2 id="match-events" className="font-display text-4xl font-bold uppercase">
              {t("match.keyEvents")}
            </h2>
            <ul className="mt-5 divide-y divide-border border-y border-border">
              {match.events.map((event) => (
                <li
                  key={event.id}
                  className="grid grid-cols-[3rem_minmax(0,1fr)] items-start gap-x-3 gap-y-1 py-4 sm:grid-cols-[3rem_7.5rem_minmax(0,1fr)] sm:items-center sm:gap-x-4"
                >
                  <span className="tabular-nums text-muted-foreground">
                    {event.minute === null ? "—" : `${event.minute}'`}
                  </span>
                  <span className="inline-flex items-center gap-2 font-semibold">
                    <span aria-hidden="true">
                      {event.event_type === "goal"
                        ? "⚽"
                        : event.event_type === "yellow_card"
                          ? "🟨"
                          : "🟥"}
                    </span>
                    <span
                      className={
                        event.event_type === "goal"
                          ? "text-foreground"
                          : event.event_type === "yellow_card"
                            ? "text-yellow-500"
                            : "text-red-500"
                      }
                    >
                      {t(
                        event.event_type === "goal"
                          ? "match.goal"
                          : event.event_type === "yellow_card"
                            ? "match.yellowCard"
                            : "match.redCard",
                      )}
                    </span>
                  </span>
                  <div className="col-start-2 flex min-w-0 flex-wrap items-center gap-x-4 gap-y-1 sm:col-start-auto">
                    <span className="font-semibold">
                      {localizedPlayerName(
                        event.player_name ?? t("match.unknownScorer"),
                        event.player_chinese_name,
                        language,
                      )}
                    </span>
                    {event.assist_player_name && (
                      <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
                        <span aria-hidden="true">🎯</span>
                        <span>
                          {t("match.assistedBy", {
                            name: localizedPlayerName(
                              event.assist_player_name,
                              event.assist_player_chinese_name,
                              language,
                            ),
                          })}
                        </span>
                      </span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )}
        {match.description && (
          <section className="mt-10" aria-labelledby="match-description">
            <h2 id="match-description" className="font-display text-4xl font-bold uppercase">
              {t("match.description")}
            </h2>
            <p className="mt-5 whitespace-pre-line leading-7 text-muted-foreground">
              {match.description}
            </p>
          </section>
        )}
        <section className="mt-10" aria-labelledby="match-photos">
          <h2 id="match-photos" className="font-display text-4xl font-bold uppercase">
            {t("media.photos")}
          </h2>
          {account.data?.role === "admin" ? (
            <div className="mt-5 flex flex-wrap items-center gap-3 border border-border bg-card p-4">
              <input
                ref={photoInput}
                disabled={photoPending}
                multiple
                accept="image/png,image/jpeg,image/webp"
                type="file"
                onChange={(e) => setPhotoFiles(Array.from(e.target.files ?? []).slice(0, 20))}
              />
              <button
                type="button"
                disabled={!photoFiles.length || photoPending}
                className="bg-primary px-4 py-2 text-sm font-bold disabled:opacity-50"
                onClick={async () => {
                  if (uploading.current) return;
                  uploading.current = true;
                  setPhotoPending(true);
                  setPhotoError(null);
                  try {
                    await uploadPhotos(
                      `/matches/${match.id}/photos`,
                      photoFiles,
                      () => setPhotoFiles((remaining) => remaining.slice(1)),
                      {
                        alt: `${match.home.name} — ${match.away.name}`,
                      },
                    );
                    if (photoInput.current) photoInput.current.value = "";
                  } catch (error) {
                    if (error instanceof PhotoUploadError) setPhotoError(error.fileName);
                  } finally {
                    await query.refetch();
                    uploading.current = false;
                    setPhotoPending(false);
                  }
                }}
              >
                {photoPending ? t("media.uploading") : t("media.addPhotos")}
              </button>
              {photoError ? (
                <p role="alert" className="w-full text-copper">
                  {t("media.uploadError")} {photoError}
                </p>
              ) : null}
            </div>
          ) : null}
          {match.photos.length ? (
            <div className="mt-6">
              <PhotoGrid photos={match.photos} />
            </div>
          ) : null}
        </section>
        <section className="mt-10" aria-labelledby="match-highlights">
          <h2 id="match-highlights" className="font-display text-4xl font-bold uppercase">
            {t("match.highlights")}
          </h2>
          {account.data?.role === "admin" && (
            <HighlightEditor matchId={match.id} videos={match.videos} />
          )}
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
        <MatchRatingsSection matchId={match.id} final={match.status === "final"} />
      </div>
    </>
  );
}
