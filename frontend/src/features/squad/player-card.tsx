import { useState, type ReactNode } from "react";
import { useI18n } from "@/i18n/i18n-provider";
import type { Player } from "@/types/football";
export function PlayerCard({ player, actions }: { player: Player; actions?: ReactNode }) {
  const { c, t } = useI18n();
  const [failedPhoto, setFailedPhoto] = useState<string | null>(null);
  const photo = player.photo_url && player.photo_url !== failedPhoto ? player.photo_url : null;
  return (
    <article
      className={`group relative overflow-hidden border border-border bg-card ${player.active ? "" : "opacity-70"}`}
    >
      <div className="relative flex aspect-[4/4.5] items-end justify-center overflow-hidden bg-secondary">
        <div className="texture absolute inset-0 opacity-70" />
        {player.shirt_number !== null && (
          <div className="absolute left-4 top-4 z-10 font-display text-5xl font-bold text-copper drop-shadow-lg">
            {String(player.shirt_number).padStart(2, "0")}
          </div>
        )}
        {photo ? (
          <img
            src={photo}
            alt={player.display_name}
            loading="lazy"
            referrerPolicy="no-referrer"
            onError={() => setFailedPhoto(photo)}
            className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
        ) : (
          <svg
            aria-hidden="true"
            viewBox="0 0 300 330"
            className="relative h-[85%] w-[85%] translate-y-8 fill-muted-foreground/20"
          >
            <circle cx="150" cy="100" r="48" />
            <path d="M70 250c0-56 28-93 80-93s80 37 80 93v100H70z" />
          </svg>
        )}
      </div>
      <div className="border-t-2 border-primary p-4 md:p-5">
        <p className="eyebrow text-copper">{c(player.position.slice(0, -1))}</p>
        <h3 className="mt-2 break-words font-display text-2xl font-bold uppercase leading-none md:text-3xl">
          {player.display_name}
        </h3>
        {!player.active && (
          <p className="mt-3 text-xs text-muted-foreground">{t("squad.inactive")}</p>
        )}
        {actions && (
          <div className="mt-4 flex flex-wrap gap-2 border-t border-border pt-4">{actions}</div>
        )}
      </div>
    </article>
  );
}
