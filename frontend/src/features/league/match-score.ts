export const isValidScore = (value: string) =>
  value.trim() === "" ||
  (Number.isInteger(Number(value)) && Number(value) >= 0 && Number(value) <= 99);

export function scoreError(home: string, away: string) {
  if (!isValidScore(home) || !isValidScore(away)) return "match.scoreRange";
  if ((home.trim() === "") !== (away.trim() === "")) return "match.scorePair";
  return null;
}
