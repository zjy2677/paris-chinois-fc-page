import { createFileRoute } from "@tanstack/react-router";
import { SquadPage } from "@/features/squad/squad-page";
export const Route = createFileRoute("/team")({ component: SquadPage });
