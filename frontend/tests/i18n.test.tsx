import { test } from "node:test";
import assert from "node:assert/strict";
import { renderToStaticMarkup } from "react-dom/server";
import { translations, type Language } from "../src/i18n/translations";
import { localizedDate, translate } from "../src/i18n/format";
import { I18nProvider } from "../src/i18n/i18n-provider";
import { LeagueTable } from "../src/features/league/league-table";
import { MatchCard } from "../src/features/league/match-card";
import { ContactForm } from "../src/features/contact/contact-form";
import { PlayerCard } from "../src/features/squad/player-card";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
const nextMatch = {
  id: "test",
  matchday: 5,
  date: "2026-10-16T20:30:00+02:00",
  home: { id: "home", name: "Home", short: "H" },
  away: { id: "away", name: "Away", short: "A" },
  stadium: "Test stadium",
  address: "",
  status: "scheduled" as const,
};
import { players } from "../src/data/players";

const languages: Language[] = ["en", "fr", "zh"];
for (const language of languages) {
  test(`${language}: complete catalog, editorial copy and interpolation`, () => {
    assert.deepEqual(
      Object.keys(translations[language]).sort(),
      Object.keys(translations.en).sort(),
    );
    for (const [key, value] of Object.entries(translations[language])) {
      assert.ok(value.trim(), key);
      assert.deepEqual(
        value.match(/\{\w+\}/g)?.sort() ?? [],
        translations.en[key as keyof typeof translations.en].match(/\{\w+\}/g)?.sort() ?? [],
        key,
      );
    }
    assert.equal(
      translate(language, "Matchday {number}", { number: 5 }),
      { en: "Matchday 5", fr: "Journée 5", zh: "第5轮" }[language],
    );
  });
  test(`${language}: components render translated labels and retain stable form values`, () => {
    const markup = renderToStaticMarkup(
      <QueryClientProvider client={new QueryClient()}>
        <I18nProvider initialLanguage={language}>
          <LeagueTable />
          <MatchCard match={nextMatch} />
          <ContactForm />
          <PlayerCard player={players[0]!} />
        </I18nProvider>
      </QueryClientProvider>,
    );
    for (const key of ["Email address", "Send message", "Home", "Away"] as const)
      assert.ok(markup.includes(translations[language][key]), key);
    assert.ok(markup.includes('value="general"'));
    assert.ok(markup.includes("20:30"));
    if (language !== "en") {
      assert.ok(!markup.includes("Send message"));
    }
  });
  test(`${language}: dates preserve Paris kickoff before and after DST`, () => {
    assert.equal(
      localizedDate(language, nextMatch.date, {
        hour: "2-digit",
        minute: "2-digit",
        hourCycle: "h23",
      }),
      "20:30",
    );
    assert.equal(
      localizedDate(language, "2026-11-06T19:00:00+01:00", {
        hour: "2-digit",
        minute: "2-digit",
        hourCycle: "h23",
      }),
      "19:00",
    );
    const sampleDate = localizedDate(language, "2026-10-10", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
    assert.ok(sampleDate.includes({ en: "October", fr: "octobre", zh: "10月" }[language]));
  });
}
