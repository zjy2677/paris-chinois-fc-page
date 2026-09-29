import { createFileRoute } from "@tanstack/react-router";
import { BlogDetailPage } from "@/features/blog/blog-detail-page";

export const Route = createFileRoute("/blog_/$postId")({ component: BlogPostRoute });

function BlogPostRoute() {
  const { postId } = Route.useParams();
  return <BlogDetailPage id={postId} />;
}
