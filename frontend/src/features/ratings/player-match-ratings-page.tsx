import { Link } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { PageIntro } from "@/components/layout/page-intro";
import { assets } from "@/config/assets";
import { useAccount } from "@/features/auth/auth-api";
import { useMatch } from "@/features/league/league-api";
import { PlayerPortrait } from "@/features/squad/player-portrait";
import { playerPhotoUrl } from "@/features/squad/squad-api";
import { useI18n } from "@/i18n/i18n-provider";
import { localizedPlayerName } from "@/lib/player-name";
import {
  deleteRating,
  RatingError,
  saveRating,
  useMyRating,
  usePlayerRatings,
} from "./ratings-api";
import { StarRating } from "./star-rating";

export function PlayerMatchRatingsPage({
  matchId,
  playerId,
}: {
  matchId: string;
  playerId: string;
}) {
  const { t, language, formatDate } = useI18n();
  const account = useAccount();
  const match = useMatch(matchId);
  const ratings = usePlayerRatings(matchId, playerId);
  const canRate = account.data?.role === "player" || account.data?.role === "admin";
  const mine = useMyRating(matchId, playerId, canRate);
  const client = useQueryClient();
  const [stars, setStars] = useState<number | null>(null);
  const [comment, setComment] = useState("");
  useEffect(() => {
    if (!mine.isSuccess) return;
    setStars(mine.data?.stars ?? null);
    setComment(mine.data?.comment ?? "");
  }, [mine.isSuccess, mine.data]);
  const refresh = async () => {
    await Promise.all([
      client.invalidateQueries({ queryKey: ["ratings", matchId, playerId] }),
      client.invalidateQueries({ queryKey: ["ratings", matchId] }),
    ]);
  };
  const save = useMutation({
    mutationFn: () =>
      saveRating(matchId, playerId, { stars: stars!, comment: comment.trim() || null }),
    onSuccess: refresh,
  });
  const remove = useMutation({
    mutationFn: () => deleteRating(matchId, playerId),
    onSuccess: refresh,
  });
  const player = ratings.data?.summary;
  const name = player
    ? localizedPlayerName(player.display_name, player.chinese_name, language)
    : t("ratings.title");
  const matchTitle = match.data ? `${match.data.home.name} — ${match.data.away.name}` : "";
  return (
    <>
      <PageIntro backgroundImage={assets.league} eyebrow={matchTitle} title={name} />
      <main className="site-container py-12 md:py-16">
        <Link
          to="/matches/$id"
          params={{ id: matchId }}
          className="text-sm text-copper underline underline-offset-4"
        >
          {t("ratings.back")}
        </Link>
        {ratings.isPending ? (
          <p className="mt-10">{t("ratings.loading")}</p>
        ) : ratings.isError ? (
          <p role="alert" className="mt-10 text-copper">
            {ratings.error instanceof RatingError && ratings.error.status === 404
              ? t("ratings.notFound")
              : t("ratings.loadError")}
          </p>
        ) : (
          <>
            <section className="mt-8 flex flex-col gap-6 border border-border bg-card p-5 sm:flex-row sm:items-center sm:p-7">
              <div className="w-28 shrink-0 overflow-hidden rounded">
                <PlayerPortrait
                  compact
                  name={name}
                  photoUrl={playerPhotoUrl({ ...ratings.data.summary, id: player!.player_id })}
                  number={player!.shirt_number}
                />
              </div>
              <div>
                <h2 className="font-display text-3xl font-bold">{name}</h2>
                <p className="mt-1 text-sm font-bold uppercase tracking-wide text-copper">
                  {t(`ratings.${player!.participation}`)}
                </p>
                <div className="mt-3 flex flex-wrap items-center gap-3">
                  <StarRating
                    value={player!.average_stars}
                    label={
                      player!.average_stars === null
                        ? t("ratings.unrated")
                        : t("ratings.starLabel", { score: player!.average_stars })
                    }
                  />
                  <span className="text-2xl font-bold tabular-nums">
                    {player!.average_stars?.toFixed(1) ?? "—"}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {t(player!.rating_count === 1 ? "ratings.countOne" : "ratings.count", {
                      count: player!.rating_count,
                    })}
                  </span>
                </div>
              </div>
            </section>
            <section className="mt-10" aria-labelledby="your-rating">
              <h2 id="your-rating" className="font-display text-3xl font-bold">
                {t("ratings.yourRating")}
              </h2>
              {canRate ? (
                mine.isPending ? (
                  <p className="mt-4 text-muted-foreground">{t("ratings.loading")}</p>
                ) : mine.isError ? (
                  <p role="alert" className="mt-4 text-copper">
                    {t("ratings.loadError")}
                  </p>
                ) : (
                  <form
                    className="mt-5 max-w-2xl border border-border bg-card p-5"
                    onSubmit={(event) => {
                      event.preventDefault();
                      if (stars !== null && !save.isPending) save.mutate();
                    }}
                  >
                    <StarRating
                      value={stars}
                      label={t("ratings.chooseStars")}
                      onChange={setStars}
                    />
                    <label className="mt-5 block text-sm font-semibold" htmlFor="rating-comment">
                      {t("ratings.comment")}
                    </label>
                    <textarea
                      id="rating-comment"
                      value={comment}
                      maxLength={500}
                      onChange={(event) => setComment(event.target.value)}
                      rows={4}
                      className="mt-2 w-full rounded border border-border bg-background p-3 focus:border-copper focus:outline-none"
                    />
                    <div className="mt-4 flex flex-wrap gap-3">
                      <button
                        type="submit"
                        disabled={stars === null || save.isPending || remove.isPending}
                        className="bg-primary px-5 py-2 font-bold disabled:opacity-50"
                      >
                        {save.isPending ? t("ratings.saving") : t("ratings.save")}
                      </button>
                      {mine.data && (
                        <button
                          type="button"
                          disabled={save.isPending || remove.isPending}
                          onClick={() => remove.mutate()}
                          className="border border-border px-5 py-2 disabled:opacity-50"
                        >
                          {t("ratings.remove")}
                        </button>
                      )}
                    </div>
                    {(save.isError || remove.isError) && (
                      <p role="alert" className="mt-3 text-sm text-copper">
                        {t(remove.isError ? "ratings.removeError" : "ratings.saveError")}
                      </p>
                    )}
                  </form>
                )
              ) : (
                <p className="mt-4 text-muted-foreground">{t("ratings.membersOnly")}</p>
              )}
            </section>
            <section className="mt-12" aria-labelledby="all-ratings">
              <h2 id="all-ratings" className="font-display text-3xl font-bold">
                {t("ratings.comments")}
              </h2>
              {ratings.data.ratings.length === 0 ? (
                <p className="mt-4 text-muted-foreground">{t("ratings.noRatings")}</p>
              ) : (
                <ul className="mt-5 divide-y divide-border border-y border-border">
                  {ratings.data.ratings.map((rating) => (
                    <li key={rating.id} id={`comment-${rating.id}`} className="py-5">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-semibold">{rating.author_name}</span>
                        <time
                          className="text-xs text-muted-foreground"
                          dateTime={rating.created_at}
                        >
                          {formatDate(rating.created_at, { dateStyle: "medium" })}
                        </time>
                      </div>
                      <div className="mt-2">
                        <StarRating
                          value={rating.stars}
                          label={t("ratings.starLabel", { score: rating.stars })}
                        />
                      </div>
                      {rating.comment && (
                        <p className="mt-3 whitespace-pre-wrap break-words text-muted-foreground">
                          {rating.comment}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        )}
      </main>
    </>
  );
}
