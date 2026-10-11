import { test } from "node:test";
import assert from "node:assert/strict";
import { renderToStaticMarkup } from "react-dom/server";
import { I18nProvider } from "../src/i18n/i18n-provider";
import { BoardPlayerIcon, PlayerStats } from "../src/features/formations/board-player";
import { countdown, placePlayer } from "../src/features/formations/formation-utils";

test("positions survive moves without duplicate players and bench clears coordinates", () => {
  let items = placePlayer([], "one", "pitch", 22.5, 80);
  items = placePlayer(items, "one", "pitch", -10, 110);
  assert.deepEqual(items, [{ player_id: "one", placement: "pitch", x: 0, y: 100 }]);
  items = placePlayer(items, "one", "bench");
  assert.deepEqual(items, [{ player_id: "one", placement: "bench", x: null, y: null }]);
});
test("countdown handles unknown dates and never becomes negative", () => {
  assert.equal(countdown(null, 0), null);
  assert.equal(countdown("invalid", 0), null);
  assert.deepEqual(countdown("2026-10-09T12:00:00Z", Date.parse("2026-10-09T13:00:00Z")), {
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0,
  });
  assert.deepEqual(countdown("2026-10-10T13:01:02Z", Date.parse("2026-10-09T12:00:00Z")), {
    days: 1,
    hours: 1,
    minutes: 1,
    seconds: 2,
  });
});
test("player stats reuse goal and assist icons and omit zero counts", () => {
  const html = renderToStaticMarkup(
    <I18nProvider>
      <PlayerStats goals={2} assists={1} />
    </I18nProvider>,
  );
  assert.ok(html.includes("⚽ 2"));
  assert.ok(html.includes("🎯 1"));
  const empty = renderToStaticMarkup(
    <I18nProvider>
      <PlayerStats goals={0} assists={0} />
    </I18nProvider>,
  );
  assert.ok(!empty.includes("⚽"));
  assert.ok(!empty.includes("🎯"));
});

test("rated squad icons show their match average over the portrait", () => {
  const player = {
    id: "player-one",
    display_name: "Player One",
    chinese_name: null,
    photo_url: null,
    has_uploaded_photo: false,
    shirt_number: 8,
    description: null,
    position: "Midfielders",
    goals: 0,
    assists: 0,
  };
  const rated = renderToStaticMarkup(
    <I18nProvider>
      <BoardPlayerIcon player={player} rating={4.5} />
    </I18nProvider>,
  );
  assert.ok(rated.includes("★ 4.5"));
  const unrated = renderToStaticMarkup(
    <I18nProvider>
      <BoardPlayerIcon player={player} rating={null} />
    </I18nProvider>,
  );
  assert.ok(!unrated.includes("★"));
});
