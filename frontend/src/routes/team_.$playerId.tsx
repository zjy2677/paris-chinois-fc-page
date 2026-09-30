import { createFileRoute } from "@tanstack/react-router";
import { PlayerProfilePage } from "@/features/squad/player-profile-page";

export const Route = createFileRoute("/team_/$playerId")({ component: PlayerRoute });

function PlayerRoute() {
  const { playerId } = Route.useParams();
  return <PlayerProfilePage id={playerId.startsWith("player_") ? playerId.slice(7) : "invalid"} />;
}
