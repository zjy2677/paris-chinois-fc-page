import { useRouterState } from "@tanstack/react-router";
import { useI18n } from "./i18n-provider";
import type { TranslationKey } from "./translations";

const pages: Record<string, { title: TranslationKey; description: TranslationKey }> = {
  "/": { title: "home", description: "A football community with Paris at its heart." },
  "/league": {
    title: "league",
    description: "The next ninety minutes, the last whistle and everything in between.",
  },
  "/team": {
    title: "The squad",
    description: "2026/2027 season squad",
  },
  "/about": {
    title: "about.club",
    description: "about.intro",
  },
  "/contact": {
    title: "contact",
    description: "Want to connect with the club? Leave a note here.",
  },
};

export function LocaleHead() {
  const path =
    useRouterState({ select: (state) => state.location.pathname }).replace(/\/$/, "") || "/";
  const { t } = useI18n();
  const page = pages[path];
  const match = path.startsWith("/matches/");
  const player = path.startsWith("/team/player_");
  const title = `${player ? t("profile.label") : match ? t("match.details") : t(page?.title ?? "Page not found")} — Paris Chinois FC`;
  const description = t(
    (player ? "profile.description" : match ? "match.highlights" : page?.description) ??
      "The page you're looking for doesn't exist or has been moved.",
  );
  return (
    <>
      <title>{title}</title>
      <meta name="description" content={description} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:type" content="website" />
      <meta name="twitter:card" content="summary_large_image" />
    </>
  );
}
