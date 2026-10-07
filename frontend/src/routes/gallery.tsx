import { createFileRoute } from "@tanstack/react-router";
import { GalleryPage } from "@/features/gallery/gallery-page";

export const Route = createFileRoute("/gallery")({ component: GalleryPage });
