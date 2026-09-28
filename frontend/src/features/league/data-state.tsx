import { useI18n } from "@/i18n/i18n-provider";
import type { TranslationKey } from "@/i18n/translations";
export function DataState({
  loading,
  error,
  empty = "league.empty",
  retry,
}: {
  loading?: boolean;
  error?: boolean;
  empty?: TranslationKey;
  retry?: () => void;
}) {
  const { t } = useI18n();
  return (
    <div
      role={error ? "alert" : "status"}
      className="border-t border-border py-8 text-sm text-muted-foreground"
    >
      <p>{t(loading ? "league.loading" : error ? "league.error" : empty)}</p>
      {error && retry && (
        <button onClick={retry} className="mt-3 text-copper underline">
          {t("Try again")}
        </button>
      )}
    </div>
  );
}
