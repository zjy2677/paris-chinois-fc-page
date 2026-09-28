import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useI18n } from "@/i18n/i18n-provider";
import { authRequest, type Account } from "./auth-api";
export function AccountMenu({ account }: { account: Account }) {
  const { t } = useI18n();
  const cache = useQueryClient();
  const [pending, setPending] = useState(false);
  const [failed, setFailed] = useState(false);
  return (
    <details className="relative">
      <summary className="cursor-pointer list-none border border-foreground/35 px-3 py-2 text-sm font-bold uppercase text-foreground">
        {t("auth.account")}
      </summary>
      <div className="absolute right-0 mt-3 w-64 border border-border bg-card p-5 shadow-xl">
        <p className="break-all text-sm">{account.email}</p>
        <p className="mt-2 text-xs text-copper">{t(`auth.role.${account.role}`)}</p>
        <button
          type="button"
          disabled={pending}
          className="mt-4 text-sm underline disabled:opacity-50"
          onClick={async () => {
            setPending(true);
            setFailed(false);
            try {
              await authRequest<void>("logout");
              await cache.cancelQueries({ queryKey: ["auth", "me"] });
              cache.setQueryData(["auth", "me"], null);
            } catch {
              setFailed(true);
            } finally {
              setPending(false);
            }
          }}
        >
          {t(pending ? "auth.pending" : "auth.logout")}
        </button>
        {failed && (
          <p role="alert" className="mt-3 text-sm text-copper">
            {t("auth.unavailable")}
          </p>
        )}
      </div>
    </details>
  );
}
