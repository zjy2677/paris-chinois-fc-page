import { useI18n } from "@/i18n/i18n-provider";

export const inputClass =
  "mt-1.5 h-11 w-full border border-border bg-background px-3 text-base text-foreground";
export function RegistrationFields({ pending }: { pending: boolean }) {
  const { t, language } = useI18n();
  return (
    <>
      <div className="grid grid-cols-2 gap-4">
        {(language === "zh"
          ? (["last_name", "first_name"] as const)
          : (["first_name", "last_name"] as const)
        ).map((name) => (
          <label key={name} className="block min-w-0 text-sm">
            {t(name === "first_name" ? "auth.firstName" : "auth.lastName")}
            <input
              className={inputClass}
              name={name}
              autoComplete={name === "first_name" ? "given-name" : "family-name"}
              required
              maxLength={80}
              disabled={pending}
            />
          </label>
        ))}
      </div>
      <label className="block text-sm">
        {t("auth.age")}
        <input
          className={inputClass}
          name="age"
          type="number"
          inputMode="numeric"
          min={1}
          max={120}
          step={1}
          required
          disabled={pending}
          aria-describedby="age-hint"
        />
      </label>
      <span id="age-hint" className="mt-1 block text-xs text-muted-foreground">
        {t("auth.ageHint")}
      </span>
    </>
  );
}
