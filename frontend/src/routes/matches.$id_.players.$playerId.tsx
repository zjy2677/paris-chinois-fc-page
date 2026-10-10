import { createFileRoute } from "@tanstack/react-router";
import { PlayerMatchRatingsPage } from "@/features/ratings/player-match-ratings-page";

export const Route = createFileRoute("/matches/$id_/players/$playerId")({
  component: PlayerRatingsRoute,
});

function PlayerRatingsRoute() {
  const { id, playerId } = Route.useParams();
  return <PlayerMatchRatingsPage matchId={id} playerId={playerId} />;
}
