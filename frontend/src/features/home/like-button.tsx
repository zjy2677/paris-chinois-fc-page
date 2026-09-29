import { useEffect, useRef, useState } from "react";
import { Heart } from "lucide-react";
import { useI18n } from "@/i18n/i18n-provider";
import { useHomepageLikes, useToggleHomepageLike } from "./like-api";

export function LikeButton() {
  const { t } = useI18n();
  const likes = useHomepageLikes();
  const toggle = useToggleHomepageLike();
  const [celebrating, setCelebrating] = useState(false);
  const celebrationTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const liked = likes.data?.liked ?? false;

  useEffect(
    () => () => {
      if (celebrationTimer.current) clearTimeout(celebrationTimer.current);
    },
    [],
  );

  function handleToggle() {
    toggle.mutate(liked, {
      onSuccess: () => {
        if (liked) return;
        if (celebrationTimer.current) clearTimeout(celebrationTimer.current);
        setCelebrating(false);
        requestAnimationFrame(() => setCelebrating(true));
        celebrationTimer.current = setTimeout(() => setCelebrating(false), 700);
      },
    });
  }

  return (
    <div className="flex min-h-14 flex-wrap items-center gap-3">
      <button
        type="button"
        aria-pressed={liked}
        aria-label={liked ? t("home.unlike") : t("home.like")}
        disabled={!likes.data || toggle.isPending}
        onClick={handleToggle}
        className={`group relative inline-flex h-12 items-center gap-3 overflow-visible rounded-full border px-5 text-xs font-bold uppercase tracking-wider backdrop-blur-sm transition-[transform,background-color,border-color,color] duration-200 hover:-translate-y-0.5 active:translate-y-0 active:scale-95 disabled:cursor-not-allowed disabled:opacity-60 ${
          liked
            ? "border-primary bg-primary/20 text-foreground shadow-[0_0_28px_color-mix(in_oklch,var(--primary)_28%,transparent)]"
            : "border-foreground/45 bg-background/40 hover:border-copper hover:bg-background/65 hover:text-copper"
        }`}
      >
        <span className="relative grid size-7 place-items-center" aria-hidden="true">
          {celebrating ? (
            <span className="like-burst">
              {Array.from({ length: 8 }, (_, index) => (
                <i key={index} />
              ))}
            </span>
          ) : null}
          <Heart
            size={21}
            className={`relative z-10 transition-[transform,fill,color] duration-300 group-hover:scale-110 ${
              liked ? "scale-110 fill-primary text-primary" : "text-current"
            } ${celebrating ? "animate-[like-heart-pop_.55s_ease-out]" : ""}`}
          />
        </span>
        <span>{liked ? t("home.liked") : t("home.like")}</span>
        <span
          aria-live="polite"
          aria-label={t("home.likeCount", { count: likes.data?.count ?? 0 })}
          className={`min-w-8 rounded-full bg-foreground/10 px-2 py-1 text-center tabular-nums transition-[transform,background-color] duration-300 ${
            celebrating ? "scale-125 bg-primary/35" : ""
          }`}
        >
          {likes.data?.count ?? "—"}
        </span>
      </button>
      {toggle.isError ? (
        <span className="text-xs text-copper" role="status">
          {t("home.likeError")}
        </span>
      ) : null}
    </div>
  );
}
