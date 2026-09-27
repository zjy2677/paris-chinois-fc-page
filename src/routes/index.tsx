import { createFileRoute } from '@tanstack/react-router';
import { HomePage } from '@/features/home/home-page';
export const Route = createFileRoute('/')({
  head: () => ({ meta: [{ title: 'Paris Chinois FC — Two cultures. One club.' }, { name: 'description', content: 'Paris Chinois FC: fixtures, results, squad and stories from a football community in Paris.' }, { property: 'og:title', content: 'Paris Chinois FC — Two cultures. One club.' }, { property: 'og:description', content: 'Fixtures, results, squad and stories from a football community in Paris.' }, { property: 'og:type', content: 'website' }, { name: 'twitter:card', content: 'summary_large_image' }] }),
  component: HomePage,
});
