import { Link } from "@tanstack/react-router";
import { ArrowUpRight } from "lucide-react";
import { useI18n } from "@/i18n/i18n-provider";
import type { BlogPost } from "./blog-api";
import { mediaUrl } from "@/features/gallery/media-api";

export function BlogCard({ post }: { post: BlogPost }) {
  const { t, formatDate } = useI18n();
  return (
    <article className="flex min-h-64 flex-col overflow-hidden border border-border bg-card transition-colors hover:border-copper/70">
      {post.photos?.[0] ? (
        <img
          src={mediaUrl(post.photos[0].url)}
          alt={post.photos[0].alt_text}
          className="aspect-[16/9] w-full object-cover"
          loading="lazy"
        />
      ) : null}
      <div className="flex flex-1 flex-col p-6">
        <p className="eyebrow text-copper">
          {post.published_at
            ? formatDate(post.published_at, { day: "numeric", month: "long", year: "numeric" })
            : t("blog.unpublished")}
        </p>
        <h2 className="mt-4 font-display text-4xl font-bold uppercase leading-none">
          {post.title}
        </h2>
        <Link
          to="/blog/$postId"
          params={{ postId: post.id }}
          className="mt-auto inline-flex items-center gap-2 pt-8 text-xs font-bold uppercase tracking-wider text-copper"
        >
          {t("blog.read")}
          <ArrowUpRight size={16} />
        </Link>
      </div>
    </article>
  );
}
