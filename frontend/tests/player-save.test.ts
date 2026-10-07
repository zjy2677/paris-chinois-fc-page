import { test } from "node:test";
import assert from "node:assert/strict";
import { PlayerApiError, savePlayer, type PlayerInput } from "../src/features/squad/squad-api";

const details: PlayerInput = {
  display_name: "Existing Player",
  description: "Captain",
  position: "Midfielders",
  alternate_positions: [],
  shirt_number: 8,
};

test("legacy edits omit the missing Chinese name while saving other details", async () => {
  const originalFetch = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = (async (url, options) => {
    calls++;
    assert.equal(url, "/api/players/legacy-player?season=2026%2F2027");
    assert.equal(options?.method, "PATCH");
    const payload = JSON.parse(options?.body as string);
    assert.deepEqual(payload, details);
    assert.equal(Object.hasOwn(payload, "chinese_name"), false);
    return Response.json({ ...payload, id: "legacy-player", chinese_name: null });
  }) as typeof fetch;
  try {
    const saved = await savePlayer(details, "legacy-player");
    assert.equal(saved.chinese_name, null);
    assert.equal(saved.description, "Captain");
    assert.equal(calls, 1);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("creation requires a Chinese name and sends both names", async () => {
  const originalFetch = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = (async (url, options) => {
    calls++;
    assert.equal(url, "/api/players");
    assert.equal(options?.method, "POST");
    const payload = JSON.parse(options?.body as string);
    assert.equal(payload.display_name, "Existing Player");
    assert.equal(payload.chinese_name, "张伟");
    assert.equal(payload.season, "2026/2027");
    return Response.json({ ...payload, id: "new-player" });
  }) as typeof fetch;
  try {
    for (const payload of [details, { ...details, chinese_name: " " }]) {
      await assert.rejects(
        savePlayer(payload),
        (error: unknown) => error instanceof PlayerApiError && error.status === 422,
      );
    }
    assert.equal(calls, 0);
    const saved = await savePlayer({ ...details, chinese_name: "张伟" });
    assert.equal(saved.chinese_name, "张伟");
    assert.equal(calls, 1);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
