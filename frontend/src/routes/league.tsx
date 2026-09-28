import { createFileRoute } from "@tanstack/react-router";
import { LeaguePage } from "@/features/league/league-page";
export const Route = createFileRoute("/league")({ component: LeaguePage });
