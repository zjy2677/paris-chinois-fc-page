import { useI18n } from "@/i18n/i18n-provider";
import crest from "@/assets/club/paris-chinois-fc-metallic.png";

export function ClubLogo({ className = "" }: { className?: string }) {
  const { t } = useI18n();

  return (
    <div
      aria-label={t("Paris Chinois FC crest")}
      className={`flex h-11 w-12 shrink-0 items-center justify-center overflow-hidden bg-transparent ${className}`}
    >
      <img src={crest} alt={t("Paris Chinois FC crest")} className="h-full w-full object-contain" />
    </div>
  );
}
