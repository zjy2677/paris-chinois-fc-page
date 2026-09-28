import { useI18n } from "@/i18n/i18n-provider";
import { Button } from "@/components/ui/button";
import type { Player } from "@/types/football";
export type Position = "All" | Player["position"];
const positions: Position[] = ["All", "Goalkeepers", "Defenders", "Midfielders", "Forwards"];
export function PositionFilter({
  value,
  onChange,
}: {
  value: Position;
  onChange: (value: Position) => void;
}) {
  const { t, c } = useI18n();
  return (
    <div
      className="flex gap-2 overflow-x-auto pb-3"
      role="group"
      aria-label={t("Filter players by position")}
    >
      {positions.map((position) => (
        <Button
          key={position}
          variant="ghost"
          aria-pressed={value === position}
          onClick={() => onChange(position)}
          className={`shrink-0 rounded-none border px-4 text-xs font-bold uppercase tracking-wider ${value === position ? "border-primary bg-primary text-foreground hover:bg-oxblood" : "border-border text-muted-foreground hover:bg-secondary hover:text-foreground"}`}
        >
          {c(position)}
        </Button>
      ))}
    </div>
  );
}
