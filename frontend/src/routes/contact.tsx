import { createFileRoute } from "@tanstack/react-router";
import { ContactPage } from "@/features/contact/contact-page";
export const Route = createFileRoute("/contact")({ component: ContactPage });
