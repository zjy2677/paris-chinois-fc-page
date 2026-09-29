import { useState } from "react";
import { Link, useRouterState } from "@tanstack/react-router";
import { Menu, ArrowUpRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ClubLogo } from "@/components/club-logo";
import { NavigationDrawer } from "./navigation-drawer";
import { LanguageSelector } from "./language-selector";
import { useAccount } from "@/features/auth/auth-api";
import { AccountMenu } from "@/features/auth/account-menu";
import { LoginModal } from "@/features/auth/login-modal";
import { navigation } from "@/config/navigation";
import { useI18n } from "@/i18n/i18n-provider";

export function Header() {
  const account = useAccount();
  const [menuOpen, setMenuOpen] = useState(false);
  const [loginOpen, setLoginOpen] = useState(false);
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { t } = useI18n();

  return (
    <>
      <header className="absolute inset-x-0 top-0 z-30 border-b border-foreground/15 bg-background/40 backdrop-blur-sm">
        <div className="site-container grid h-20 grid-cols-[minmax(0,1fr)_auto] items-center gap-3 xl:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]">
          <div className="flex min-w-0 items-center gap-3 sm:gap-5">
            <Button
              variant="ghost"
              size="icon"
              aria-label={t("openMenu")}
              title={t("openMenu")}
              onClick={() => setMenuOpen(true)}
              className="h-11 w-11 shrink-0 rounded-none text-foreground hover:bg-secondary"
            >
              <Menu className="!h-6 !w-6" />
            </Button>
            <Link to="/" className="flex min-w-0 items-center gap-3">
              <ClubLogo />
              <span className="hidden font-display text-lg font-bold uppercase leading-none sm:block">
                Paris
                <br />
                Chinois FC
              </span>
            </Link>
          </div>
          <nav className="hidden items-center gap-6 xl:flex" aria-label={t("Primary navigation")}>
            {navigation.slice(1, 6).map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={`eyebrow whitespace-nowrap transition-colors hover:text-primary ${pathname === item.to ? "text-copper" : "text-foreground"}`}
              >
                {t(item.labelKey)}
              </Link>
            ))}
          </nav>
          <div className="flex items-center justify-end gap-2">
            <LanguageSelector />
            {account.data ? (
              <AccountMenu account={account.data} />
            ) : (
              <Button
                variant="ghost"
                onClick={() => setLoginOpen(true)}
                className="gap-2 rounded-none border border-foreground/35 px-3 sm:px-4 font-bold uppercase tracking-wider text-foreground hover:bg-secondary"
              >
                {t("login")} <ArrowUpRight className="hidden sm:block" />
              </Button>
            )}
          </div>
        </div>
      </header>
      <NavigationDrawer open={menuOpen} onOpenChange={setMenuOpen} />
      <LoginModal open={loginOpen} onOpenChange={setLoginOpen} />
    </>
  );
}
