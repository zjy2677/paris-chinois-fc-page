import { test } from "node:test";
import assert from "node:assert/strict";
import { isValidScore, scoreError } from "../src/features/league/match-score";

test("scores accept blanks and whole numbers within the API bounds", () => {
  for (const value of ["", "0", "1", "99"]) assert.equal(isValidScore(value), true);
  for (const value of ["-1", "1.5", "100", "1e309", "Infinity", "NaN", "abc"])
    assert.equal(isValidScore(value), false, value);
});

test("both scores or neither are required", () => {
  assert.equal(scoreError("", ""), null);
  assert.equal(scoreError("0", "99"), null);
  assert.equal(scoreError("0", ""), "match.scorePair");
  assert.equal(scoreError("", "0"), "match.scorePair");
  assert.equal(scoreError("1e309", "0"), "match.scoreRange");
});
