import { createFileRoute, notFound } from '@tanstack/react-router';
import { news } from '@/data/news';
import { ArticlePage } from '@/features/news/article-page';
export const Route = createFileRoute('/news/$id')({
  loader: ({ params }) => { const item = news.find(entry => entry.id === params.id); if (!item) throw notFound(); return item; },
  head: ({ loaderData }) => ({ meta: [{ title: loaderData ? `${loaderData.title} — Paris Chinois FC` : 'Story not found — Paris Chinois FC' }, { name: 'description', content: loaderData?.excerpt ?? 'The requested club story was not found.' }, { property: 'og:title', content: loaderData?.title ?? 'Story not found — Paris Chinois FC' }, { property: 'og:description', content: loaderData?.excerpt ?? 'The requested club story was not found.' }, { property: 'og:type', content: 'article' }, { name: 'twitter:card', content: 'summary_large_image' }] }),
  component: () => <ArticlePage item={Route.useLoaderData()} />,
});
