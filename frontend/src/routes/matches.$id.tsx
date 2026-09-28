import { createFileRoute } from "@tanstack/react-router";
import { MatchDetailPage } from "@/features/league/match-detail-page";
export const Route = createFileRoute("/matches/$id")({ component: MatchRoute });
function MatchRoute() {
  const { id } = Route.useParams();
  return <MatchDetailPage id={id} />;
}
