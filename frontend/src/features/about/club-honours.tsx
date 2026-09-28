import { Trophy } from "lucide-react";
import { honours } from "@/data/club-history";
import { useI18n } from "@/i18n/i18n-provider";

export function ClubHonours() {
  const { t } = useI18n();
  return (
    <section
      className="border-y border-border bg-card py-16 md:py-24"
      aria-labelledby="club-honours"
    >
      <div className="site-container">
        <p className="eyebrow text-copper">{t("about.region")}</p>
        <h2 id="club-honours" className="section-title mt-5">
          {t("about.honoursTitle")}
        </h2>
        <p className="mt-6 max-w-3xl leading-relaxed text-muted-foreground">
          {t("about.honoursIntro")}
        </p>
        <ul className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {honours.map((honour) => (
            <li key={honour.name} className="border border-border bg-background/40 p-6 md:p-8">
              <div className="flex items-center gap-3 text-copper">
                <Trophy size={20} aria-hidden="true" />
                <span className="eyebrow">{t("about.champions")}</span>
              </div>
              <h3 className="mt-6 font-display text-3xl font-bold leading-tight">
                {t(honour.name)}
              </h3>
              <p className="mt-5 text-sm leading-loose tabular-nums text-muted-foreground">
                {honour.years.join(" · ")}
              </p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
