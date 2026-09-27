const milestones = [
  { label: 'The beginning', title: 'A place to belong', body: 'Placeholder milestone — add the club’s real founding story and date here.' },
  { label: 'The community', title: 'Growing together', body: 'Placeholder milestone — share a meaningful moment from the club’s journey.' },
  { label: 'The next chapter', title: 'Looking forward', body: 'Placeholder milestone — describe the club’s ambitions in its own words.' },
];
export function ClubTimeline() { return <div className="mt-10 grid gap-0 md:grid-cols-3">{milestones.map((step, index) => <div key={step.label} className="border-t border-border py-7 md:pr-10"><span className="font-display text-4xl font-bold text-primary">0{index + 1}</span><p className="eyebrow mt-5 text-copper">{step.label}</p><h3 className="mt-2 font-display text-3xl font-bold uppercase">{step.title}</h3><p className="mt-3 text-sm leading-relaxed text-muted-foreground">{step.body}</p></div>)}</div>; }
