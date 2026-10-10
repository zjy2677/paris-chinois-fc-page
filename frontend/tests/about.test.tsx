import { test } from "node:test";
import assert from "node:assert/strict";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderToStaticMarkup } from "react-dom/server";
import { AboutPage } from "../src/features/about/about-page";
import { I18nProvider } from "../src/i18n/i18n-provider";
import { translations, type Language } from "../src/i18n/translations";
import { honours } from "../src/data/club-history";

for (const language of ["en", "fr", "zh"] as Language[]) {
  test(`About ${language}: club history, six honours and real photography`, () => {
    const html = renderToStaticMarkup(
      <QueryClientProvider client={new QueryClient()}>
        <I18nProvider initialLanguage={language}>
          <AboutPage />
        </I18nProvider>
      </QueryClientProvider>,
    );
    assert.ok(html.includes(translations[language]["about.history1"]));
    assert.ok(html.includes(translations[language]["about.brothers"]));
    assert.ok(html.includes("Jonathan Petersson"));
    assert.ok(html.includes("about-pitch.jpg"));
    assert.ok(!html.includes("club-training.jpg"));
    for (const honour of honours) {
      assert.ok(html.includes(translations[language][honour.name]));
      assert.ok(html.includes(honour.years.join(" · ")));
    }
    assert.ok(!html.includes("Placeholder milestone"));
  });
}
test("All championship years match the supplied history", () => {
  assert.deepEqual(
    honours.map((item) => item.years),
    [
      [2014, 2015, 2018, 2019, 2022, 2024, 2025],
      [2016],
      [2016, 2017],
      [2016, 2017, 2018],
      [2023],
      [2023],
    ],
  );
});

test("About hides the fallback photo credit when album backgrounds are active", () => {
  const queryClient = new QueryClient();
  queryClient.setQueryData(["media", "backgrounds"], {
    album_id: "album-1",
    interval_seconds: 8,
    transition: "fade",
    photos: [
      {
        id: "photo-1",
        url: "/api/media/photos/photo-1/content",
        caption: null,
        alt_text: "Team photo",
        use_as_background: true,
      },
    ],
  });
  const html = renderToStaticMarkup(
    <QueryClientProvider client={queryClient}>
      <I18nProvider initialLanguage="en">
        <AboutPage />
      </I18nProvider>
    </QueryClientProvider>,
  );
  assert.ok(html.includes("/api/media/photos/photo-1/content"));
  assert.ok(!html.includes("Jonathan Petersson"));
});
