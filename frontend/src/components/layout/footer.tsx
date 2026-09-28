import { Link } from "@tanstack/react-router";
import { ClubLogo } from "@/components/club-logo";
import { navigation } from "@/config/navigation";
import { useI18n } from "@/i18n/i18n-provider";

export function Footer() {
  const { t } = useI18n();
  return (
    <footer className="border-t border-border bg-card">
      <div className="site-container grid gap-12 py-16 md:grid-cols-[1fr_1fr]">
        <div>
          <div className="flex items-center gap-4">
            <ClubLogo />
            <strong className="font-display text-3xl uppercase">Paris Chinois FC</strong>
          </div>
        </div>
        <nav
          aria-label={t("Footer navigation")}
          className="grid grid-cols-2 gap-x-6 gap-y-3 self-start text-sm"
        >
          {navigation.map((item) => (
            <Link key={item.to} to={item.to} className="hover:text-copper">
              {t(item.labelKey)}
            </Link>
          ))}
        </nav>
      </div>
      <div className="site-container flex flex-col justify-between gap-3 border-t border-border py-5 text-xs text-muted-foreground sm:flex-row">
        <span>© 2026 Paris Chinois FC</span>
      </div>
    </footer>
  );
}
