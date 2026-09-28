import { Languages } from "lucide-react";
import { languageOptions } from "@/i18n/translations";
import { useI18n } from "@/i18n/i18n-provider";

export function LanguageSelector() {
  const { language, setLanguage, t } = useI18n();

  return (
    <label className="inline-flex h-11 items-center gap-1 border border-foreground/25 px-2 text-foreground transition-colors hover:border-copper hover:text-copper sm:gap-2 sm:px-3">
      <Languages className="hidden h-4 w-4 shrink-0 sm:block" aria-hidden="true" />
      <span className="sr-only">{t("language")}</span>
      <select
        aria-label={t("language")}
        value={language}
        onChange={(event) => setLanguage(event.target.value as typeof language)}
        className="cursor-pointer appearance-none bg-transparent text-xs font-bold uppercase tracking-wider outline-none"
      >
        {languageOptions.map((option) => (
          <option key={option.code} value={option.code} className="bg-card text-foreground">
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
