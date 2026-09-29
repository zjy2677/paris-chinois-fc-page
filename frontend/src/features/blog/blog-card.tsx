import { Link } from "@tanstack/react-router";
import { ArrowUpRight } from "lucide-react";
import { useI18n } from "@/i18n/i18n-provider";
import type { BlogPost } from "./blog-api";

export function BlogCard({ post }: { post: BlogPost }) {
  const { t, formatDate } = useI18n();
  return (
    <article className="flex min-h-64 flex-col border border-border bg-card p-6 transition-colors hover:border-copper/70">
      <p className="eyebrow text-copper">
        {post.published_at
          ? formatDate(post.published_at, { day: "numeric", month: "long", year: "numeric" })
          : t("blog.unpublished")}
      </p>
      <h2 className="mt-4 font-display text-4xl font-bold uppercase leading-none">{post.title}</h2>
      <Link
        to="/blog/$postId"
        params={{ postId: post.id }}
        className="mt-auto inline-flex items-center gap-2 pt-8 text-xs font-bold uppercase tracking-wider text-copper"
      >
        {t("blog.read")}
        <ArrowUpRight size={16} />
      </Link>
    </article>
  );
}
