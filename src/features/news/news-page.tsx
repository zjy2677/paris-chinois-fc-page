import { useState } from 'react';
import { PageIntro } from '@/components/layout/page-intro';
import { Button } from '@/components/ui/button';
import { news } from '@/data/news';
import type { NewsItem } from '@/types/news';
import { NewsCard } from './news-card';
type Category = 'All' | NewsItem['category'];
const categories: Category[] = ['All','Match report','Club news','Photos','Video'];
export function NewsPage() { const [category, setCategory] = useState<Category>('All'); const filtered = news.filter(item => category === 'All' || item.category === category); return <><PageIntro eyebrow="The club journal" title="News / Media" description="Stories from the touchline, moments from the pitch and everything around the club."/><section className="site-container py-16 md:py-24"><div role="group" aria-label="Filter stories" className="mb-10 flex gap-2 overflow-x-auto pb-3">{categories.map(cat => <Button key={cat} variant="ghost" aria-pressed={cat === category} onClick={() => setCategory(cat)} className={`shrink-0 rounded-none border px-4 text-xs font-bold uppercase tracking-wider ${cat === category ? 'border-primary bg-primary text-foreground hover:bg-oxblood' : 'border-border text-muted-foreground hover:bg-secondary hover:text-foreground'}`}>{cat}</Button>)}</div><div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">{filtered.map(item => <NewsCard key={item.id} item={item}/>)}</div></section></>; }
