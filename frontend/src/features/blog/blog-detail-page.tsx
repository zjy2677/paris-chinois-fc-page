import { Link } from "@tanstack/react-router";
import { useI18n } from "@/i18n/i18n-provider";
import { usePublishedPost } from "./blog-api";

export function BlogDetailPage({ id }: { id: string }) {
  const { t, formatDate } = useI18n();
  const post = usePublishedPost(id);
  if (post.isPending) return <div className="site-container py-24">{t("blog.loading")}</div>;
  if (post.isError)
    return <div className="site-container py-24 text-copper">{t("blog.notFound")}</div>;
  return (
    <article className="site-container max-w-4xl py-24">
      <Link to="/blog" className="text-sm text-copper underline">
        {t("blog.back")}
      </Link>
      <p className="eyebrow mt-12 text-copper">
        {post.data.published_at
          ? formatDate(post.data.published_at, { day: "numeric", month: "long", year: "numeric" })
          : ""}
      </p>
      <h1 className="mt-5 font-display text-6xl font-bold uppercase leading-none md:text-8xl">
        {post.data.title}
      </h1>
      <div className="mt-12 whitespace-pre-wrap text-base leading-8 md:text-lg">
        {post.data.body}
      </div>
    </article>
  );
}
