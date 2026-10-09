import type { Placement } from "./formation-api";

export function placePlayer(
  items: Placement[],
  playerId: string,
  placement: "pitch" | "bench",
  x = 50,
  y = 50,
): Placement[] {
  return [
    ...items.filter((item) => item.player_id !== playerId),
    {
      player_id: playerId,
      placement,
      x: placement === "pitch" ? Math.max(0, Math.min(100, x)) : null,
      y: placement === "pitch" ? Math.max(0, Math.min(100, y)) : null,
    },
  ];
}
export function countdown(kickoff: string | null, now: number) {
  if (!kickoff || !Number.isFinite(Date.parse(kickoff))) return null;
  const seconds = Math.max(0, Math.floor((Date.parse(kickoff) - now) / 1000));
  return {
    days: Math.floor(seconds / 86400),
    hours: Math.floor(seconds / 3600) % 24,
    minutes: Math.floor(seconds / 60) % 60,
    seconds: seconds % 60,
  };
}
