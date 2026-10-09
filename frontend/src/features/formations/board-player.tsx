import { useI18n } from "@/i18n/i18n-provider";
import { localizedPlayerName } from "@/lib/player-name";
import { PlayerPortrait } from "@/features/squad/player-portrait";
import { playerPhotoUrl } from "@/features/squad/squad-api";
import type { BoardPlayer } from "./formation-api";

export function PlayerStats({ goals, assists }: { goals: number; assists: number }) {
  const { t } = useI18n();
  return (
    <span className="flex justify-center gap-2 text-xs">
      {goals > 0 && (
        <span aria-label={t(goals === 1 ? "formation.goal" : "formation.goals", { count: goals })}>
          ⚽ {goals}
        </span>
      )}
      {assists > 0 && (
        <span
          aria-label={t(assists === 1 ? "formation.assist" : "formation.assists", {
            count: assists,
          })}
        >
          🎯 {assists}
        </span>
      )}
    </span>
  );
}
export function BoardPlayerIcon({ player }: { player: BoardPlayer }) {
  const { language } = useI18n();
  const name = localizedPlayerName(player.display_name, player.chinese_name, language);
  return (
    <>
      <span className="mx-auto block w-10 overflow-hidden rounded-full border border-copper shadow-md sm:w-12">
        <PlayerPortrait
          name={name}
          photoUrl={playerPhotoUrl(player)}
          number={player.shirt_number}
          compact
        />
      </span>
      <span
        className="mt-1 block truncate rounded bg-black/80 px-1 text-[10px] font-semibold text-white sm:text-xs"
        title={name}
      >
        {name}
      </span>
      <PlayerStats goals={player.goals} assists={player.assists} />
    </>
  );
}
