import { createFileRoute } from "@tanstack/react-router";
import { MyspacePage } from "@/features/auth/myspace-page";

export const Route = createFileRoute("/myspace/$userId")({ component: MyspacePage });
