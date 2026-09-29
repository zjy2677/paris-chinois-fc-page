import { createFileRoute } from "@tanstack/react-router";
import { BlogPage } from "@/features/blog/blog-page";

export const Route = createFileRoute("/blog")({ component: BlogPage });
