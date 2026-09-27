export function ClubLogo({ className = '' }: { className?: string }) {
  return <div aria-label="Paris Chinois FC emblem placeholder" className={`relative flex h-11 w-9 shrink-0 items-center justify-center bg-primary text-foreground ${className}`} style={{ clipPath: 'polygon(0 0, 100% 0, 100% 74%, 50% 100%, 0 74%)' }}>
    <div className="absolute inset-[3px] border border-copper" style={{ clipPath: 'polygon(0 0, 100% 0, 100% 70%, 50% 100%, 0 70%)' }} />
    <span className="relative z-10 font-display text-lg font-black leading-none text-copper">龍</span>
  </div>;
}
