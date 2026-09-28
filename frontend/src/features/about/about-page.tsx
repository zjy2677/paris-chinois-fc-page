import { useI18n } from "@/i18n/i18n-provider";
import { ClubHonours } from "./club-honours";
import { assets } from "@/config/assets";

export function AboutPage() {
  const { language, t } = useI18n();
  return (
    <>
      <section className="relative isolate overflow-hidden border-b border-border bg-background pb-20 pt-40 md:pb-28 md:pt-52">
        <img
          src={assets.about}
          alt={t("about.photoAlt")}
          width={3008}
          height={2000}
          fetchPriority="high"
          className="absolute inset-0 -z-20 h-full w-full object-cover object-center"
        />
        <div className="absolute inset-0 -z-10 bg-gradient-to-r from-black/90 via-black/65 to-black/30" />
        <div className="site-container">
          <p className="eyebrow text-copper">{t("about.since")}</p>
          <h1 className="section-title mt-6 max-w-4xl">{t("about.title")}</h1>
          {language !== "zh" && (
            <p className="mt-7 max-w-2xl text-base leading-relaxed text-foreground/90 md:text-lg">
              {t("about.intro")}
            </p>
          )}
          <a
            href="https://commons.wikimedia.org/wiki/File:Pexels-jonathan-petersson-399187.jpg"
            target="_blank"
            rel="noreferrer"
            className="mt-10 inline-block text-xs text-foreground/70 underline decoration-foreground/30 underline-offset-4 hover:text-foreground"
          >
            {t("about.photoCredit")}
          </a>
        </div>
      </section>

      <section className="site-container py-16 md:py-24" aria-labelledby="club-history">
        <div className="grid gap-10 lg:grid-cols-2 lg:gap-16">
          <div>
            <p className="eyebrow text-copper">{t("about.club")}</p>
            <h2
              id="club-history"
              className="mt-5 font-display text-4xl font-bold uppercase leading-tight md:text-5xl"
            >
              {t("about.historyTitle")}
            </h2>
            <div className="mt-7 space-y-5 leading-relaxed text-muted-foreground">
              <p>{t("about.history1")}</p>
              <p>{t("about.history2")}</p>
              <p>{t("about.history3")}</p>
            </div>
          </div>
          <figure className="self-start">
            <img
              src={assets.hero}
              alt={t("about.teamAlt")}
              width={1280}
              height={1028}
              loading="lazy"
              className="h-auto w-full border border-border"
            />
            <figcaption className="mt-3 text-xs text-muted-foreground">
              {t("about.teamCaption")}
            </figcaption>
          </figure>
        </div>
        <dl className="mt-12 grid grid-cols-1 divide-y divide-border border-y border-border sm:grid-cols-3 sm:divide-x sm:divide-y-0">
          {(
            [
              ["2005", "about.founded"],
              ["20+", "about.regularPlayers"],
              ["7 / 11", "about.formats"],
            ] as const
          ).map(([value, key]) => (
            <div key={key} className="py-7 text-center">
              <dt className="text-sm text-muted-foreground">{t(key)}</dt>
              <dd className="mt-2 font-display text-5xl font-bold text-copper">{value}</dd>
            </div>
          ))}
        </dl>
        <div className="mt-12 max-w-4xl space-y-5 leading-relaxed text-muted-foreground">
          <p>{t("about.players")}</p>
          <p>
            {t("about.values1")} {t("about.poem")} {t("about.brothers")}
          </p>
          <p>{t("about.community")}</p>
        </div>
      </section>

      <ClubHonours />

      <div className="site-container py-8 text-sm text-copper">{t("about.motto")}</div>
    </>
  );
}
