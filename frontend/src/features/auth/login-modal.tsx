import { useLocalizedValidation } from "@/i18n/use-localized-validation";
import { useI18n } from "@/i18n/i18n-provider";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { authRequest, AuthError, type Account } from "./auth-api";
import type { TranslationKey } from "@/i18n/translations";

type Mode = "login" | "create";
export function LoginModal({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { t } = useI18n();
  const validation = useLocalizedValidation();
  const cache = useQueryClient();
  const [mode, setMode] = useState<Mode>("login");
  const [pending, setPending] = useState(false);
  const [feedback, setFeedback] = useState<TranslationKey | null>(null);
  return (
    <Dialog
      open={open}
      onOpenChange={(value) => {
        if (!pending) {
          setFeedback(null);
          onOpenChange(value);
        }
      }}
    >
      <DialogContent className="max-w-md border-border bg-card p-8 text-foreground shadow-2xl">
        <DialogHeader className="text-left">
          <p className="eyebrow text-copper">{t("Members area")}</p>
          <DialogTitle className="font-display text-5xl font-bold uppercase">
            {t(mode === "login" ? "Log in" : "Create account")}
          </DialogTitle>
          <DialogDescription className="text-muted-foreground">
            {t(mode === "login" ? "auth.welcome" : "auth.registerIntro")}
          </DialogDescription>
        </DialogHeader>
        <form
          key={mode}
          {...validation}
          className="mt-5 space-y-4"
          onSubmit={async (event) => {
            event.preventDefault();
            if (pending) return;
            const form = new FormData(event.currentTarget);
            setPending(true);
            setFeedback(null);
            try {
              const account = await authRequest<Account>(mode === "create" ? "register" : "login", {
                email: String(form.get("email")),
                password: String(form.get("password")),
              });
              await cache.cancelQueries({ queryKey: ["auth", "me"] });
              cache.setQueryData(["auth", "me"], account);
              onOpenChange(false);
            } catch (error) {
              const status = error instanceof AuthError ? error.status : 0;
              setFeedback(
                status === 401
                  ? "auth.invalid"
                  : status === 409
                    ? "auth.exists"
                    : status === 429
                      ? "auth.rateLimit"
                      : status === 422
                        ? "auth.validation"
                        : "auth.unavailable",
              );
            } finally {
              setPending(false);
            }
          }}
        >
          <label className="block text-sm">
            {t("Email address")}
            <input
              name="email"
              required
              type="email"
              maxLength={254}
              autoComplete="email"
              disabled={pending}
              className="mt-2 h-12 w-full border border-border bg-background px-3 text-foreground"
              placeholder="you@example.com"
            />
          </label>
          <label className="block text-sm">
            {t("Password")}
            <input
              name="password"
              required
              minLength={mode === "create" ? 12 : 1}
              maxLength={256}
              type="password"
              autoComplete={mode === "create" ? "new-password" : "current-password"}
              disabled={pending}
              className="mt-2 h-12 w-full border border-border bg-background px-3 text-foreground"
            />
          </label>
          {mode === "create" && (
            <p className="text-xs text-muted-foreground">{t("auth.passwordHint")}</p>
          )}
          <Button
            type="submit"
            disabled={pending}
            className="h-12 w-full rounded-none bg-primary font-bold uppercase tracking-wider text-primary-foreground hover:bg-primary/85"
          >
            {t(pending ? "auth.pending" : mode === "create" ? "Create account" : "Log in")}
          </Button>
          {feedback && (
            <p role="alert" className="border-l-2 border-copper pl-3 text-sm text-copper">
              {t(feedback)}
            </p>
          )}
        </form>
        <div className="flex flex-wrap justify-between gap-3 border-t border-border pt-5 text-sm">
          {mode === "login" && (
            <Button
              variant="link"
              disabled={pending}
              className="h-auto p-0 text-muted-foreground"
              onClick={() => setFeedback("Password reset is not available yet. No email was sent.")}
            >
              {t("Forgot password?")}
            </Button>
          )}
          <Button
            variant="link"
            disabled={pending}
            className="h-auto p-0 text-copper"
            onClick={() => {
              setMode(mode === "create" ? "login" : "create");
              setFeedback(null);
            }}
          >
            {t(mode === "create" ? "Log in instead" : "Create account")}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
