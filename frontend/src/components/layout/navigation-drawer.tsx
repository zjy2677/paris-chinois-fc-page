import { Link, useRouterState } from "@tanstack/react-router";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { navigation } from "@/config/navigation";
import { useI18n } from "@/i18n/i18n-provider";

export function NavigationDrawer({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { t } = useI18n();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="left"
        className="flex w-[min(90vw,430px)] max-w-none flex-col border-border bg-background p-8 text-foreground"
      >
        <SheetTitle className="font-display text-3xl font-bold uppercase">
          Paris Chinois FC
        </SheetTitle>
        <p className="eyebrow text-copper">{t("exploreClub")}</p>
        <nav aria-label={t("Main menu")} className="mt-6 flex flex-col border-t border-border">
          {navigation.map((item, index) => (
            <Link
              key={item.to}
              to={item.to}
              onClick={() => onOpenChange(false)}
              aria-current={pathname === item.to ? "page" : undefined}
              className={`flex items-center justify-between border-b border-border py-3 font-display text-4xl font-bold uppercase transition-colors hover:text-primary ${pathname === item.to ? "text-primary" : "text-foreground"}`}
            >
              <span>{t(item.labelKey)}</span>
              <span className="font-sans text-xs text-muted-foreground">0{index + 1}</span>
            </Link>
          ))}
        </nav>
      </SheetContent>
    </Sheet>
  );
}
