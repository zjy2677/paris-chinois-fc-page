import { useState } from 'react';
import { PageIntro } from '@/components/layout/page-intro';
import { players } from '@/data/players';
import type { Player } from '@/types/football';
import { PlayerCard } from './player-card';
import { PositionFilter, type Position } from './position-filter';
export function SquadPage() { const [position, setPosition] = useState<Position>('All'); const groups: Player['position'][] = ['Goalkeepers','Defenders','Midfielders','Forwards']; return <><PageIntro eyebrow="The people behind the shirt" title="The squad" description="Different journeys. One badge. Meet the faces of our sample 2026/27 squad."/><div className="site-container py-16 md:py-24"><PositionFilter value={position} onChange={setPosition}/>{groups.filter(group => position === 'All' || position === group).map(group => <section key={group} className="mt-14"><div className="mb-7 flex items-center gap-6"><h2 className="font-display text-4xl font-bold uppercase md:text-5xl">{group}</h2><div className="h-px flex-1 bg-border"/></div><div className="grid grid-cols-2 gap-3 md:grid-cols-3 md:gap-5 xl:grid-cols-4">{players.filter(player => player.position === group).map(player => <PlayerCard key={player.id} player={player}/>)}</div></section>)}</div></>; }
