import { useI18n } from "@/i18n/i18n-provider";
import type { Player } from "@/types/football";
export function PlayerCard({ player }: { player: Player }) {
  const { c } = useI18n();
  return (
    <article className="group relative overflow-hidden border border-border bg-card">
      <div className="relative flex aspect-[4/4.5] items-end justify-center overflow-hidden bg-secondary">
        <div className="texture absolute inset-0 opacity-70" />
        <div className="absolute top-4 left-4 z-10 font-display text-5xl font-bold text-copper/75">
          {String(player.number).padStart(2, "0")}
        </div>
        <svg
          aria-hidden="true"
          viewBox="0 0 300 330"
          className="relative h-[85%] w-[85%] translate-y-8 fill-muted-foreground/20 transition-transform duration-500 group-hover:scale-105"
        >
          <circle cx="150" cy="100" r="48" />
          <path d="M70 250c0-56 28-93 80-93s80 37 80 93v100H70z" />
        </svg>
      </div>
      <div className="border-t-2 border-primary p-5">
        <p className="eyebrow text-copper">{c(player.position.slice(0, -1))}</p>
        <h3 className="mt-2 font-display text-3xl font-bold uppercase leading-none">
          {player.name}
        </h3>
      </div>
    </article>
  );
}
