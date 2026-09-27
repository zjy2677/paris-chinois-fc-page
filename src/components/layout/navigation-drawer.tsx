import { Link, useRouterState } from '@tanstack/react-router';
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog';
import { navigation } from '@/config/navigation';
export function NavigationDrawer({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const pathname = useRouterState({ select: s => s.location.pathname });
  return <Dialog open={open} onOpenChange={onOpenChange}><DialogContent className="fixed inset-y-0 left-0 top-0 h-full w-[min(90vw,430px)] max-w-none translate-x-0 translate-y-0 border-r border-border bg-background p-8 shadow-2xl sm:rounded-none [&>button]:text-foreground">
    <DialogTitle className="font-display text-3xl font-bold uppercase">Paris Chinois FC</DialogTitle><p className="eyebrow text-copper">Explore the club</p>
    <nav aria-label="Main menu" className="mt-6 flex flex-col border-t border-border">{navigation.map((item, index) => <Link key={item.to} to={item.to} onClick={() => onOpenChange(false)} aria-current={pathname === item.to ? 'page' : undefined} className={`flex items-center justify-between border-b border-border py-3 font-display text-4xl font-bold uppercase transition-colors hover:text-primary ${pathname === item.to ? 'text-primary' : 'text-foreground'}`}><span>{item.label}</span><span className="font-sans text-xs text-muted-foreground">0{index + 1}</span></Link>)}</nav>
    <p className="mt-auto text-xs text-muted-foreground">Two cultures. One club.</p>
  </DialogContent></Dialog>;
}
