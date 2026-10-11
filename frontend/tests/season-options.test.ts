import { expect, test } from "bun:test";
import { seasonOptions } from "../src/features/league/season-options";

test("groups league, cup and custom competitions by season with newest first", () => {
  const options = seasonOptions([
    { id: "old-league", season_label: "2025/2026", competition_kind: "league" },
    { id: "new-cup", season_label: "2026/2027", competition_kind: "cup" },
    { id: "new-league", season_label: "2026/2027", competition_kind: "league" },
    { id: "new-friendly", season_label: "2026/2027", competition_kind: "custom" },
  ]);

  expect(options.map((option) => option.label)).toEqual(["2026/2027", "2025/2026"]);
  expect(options[0]?.leagueId).toBe("new-league");
  expect([...options[0]!.competitionIds]).toEqual(["new-cup", "new-league", "new-friendly"]);
  expect([...options[1]!.competitionIds]).toEqual(["old-league"]);
});

test("a cup-only season has no league standing ID", () => {
  const [option] = seasonOptions([
    { id: "cup", season_label: "2024/2025", competition_kind: "cup" },
  ]);
  expect(option?.leagueId).toBeNull();
});
