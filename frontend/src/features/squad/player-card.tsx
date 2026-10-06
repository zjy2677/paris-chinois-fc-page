import type { ReactNode } from "react";
import { Link } from "@tanstack/react-router";
import { useI18n } from "@/i18n/i18n-provider";
import type { Player } from "@/types/football";
import { localizedPlayerName } from "@/lib/player-name";
import { PlayerPortrait } from "./player-portrait";
import { playerPhotoUrl } from "./squad-api";
/** Render player details, a photo with silhouette fallback, and optional management actions. */
export function PlayerCard({
  player,
  actions,
  showProfileLink = true,
}: {
  player: Player;
  actions?: ReactNode;
  showProfileLink?: boolean;
}) {
  const { c, t, language } = useI18n();
  const name = localizedPlayerName(player.display_name, player.chinese_name, language);
  return (
    <article
      className={`group relative overflow-hidden border border-border bg-card ${player.active ? "" : "opacity-70"}`}
    >
      <PlayerPortrait name={name} photoUrl={playerPhotoUrl(player)} number={player.shirt_number} />
      <div className="border-t-2 border-primary p-4 md:p-5">
        <p className="eyebrow text-copper">{c(player.position.slice(0, -1))}</p>
        {(player.alternate_positions ?? []).length > 0 && (
          <p className="mt-1 text-xs text-muted-foreground">
            {t("squad.alternateShort")}:{" "}
            {(player.alternate_positions ?? []).map((p) => c(p.slice(0, -1))).join(" · ")}
          </p>
        )}
        <h3 className="mt-2 break-words font-display text-2xl font-bold uppercase leading-none md:text-3xl">
          {showProfileLink ? (
            <Link
              to="/team/$playerId"
              params={{ playerId: `player_${player.id}` }}
              className="hover:text-copper focus-visible:outline focus-visible:outline-2 focus-visible:outline-copper"
            >
              {name}
            </Link>
          ) : (
            name
          )}
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
