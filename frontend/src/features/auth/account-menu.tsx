import { useRef, useState } from "react";
import { Link } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { useI18n } from "@/i18n/i18n-provider";
import { authRequest, avatarUrl, uploadAvatar, type Account } from "./auth-api";
export function AccountMenu({ account }: { account: Account }) {
  const { t } = useI18n();
  const cache = useQueryClient();
  const [pending, setPending] = useState(false);
  const [failed, setFailed] = useState(false);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const photo = avatarUrl(account);
  return (
    <details className="relative">
      <summary className="cursor-pointer list-none border border-foreground/35 px-3 py-2 text-sm font-bold uppercase text-foreground">
        {t("auth.account")}
      </summary>
      <div className="absolute right-0 mt-3 w-64 border border-border bg-card p-5 shadow-xl">
        <div className="flex items-center gap-3">
          {photo ? (
            <img src={photo} alt="" className="h-12 w-12 rounded-full object-cover" />
          ) : (
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-secondary text-lg font-bold">
              {account.email.slice(0, 1).toUpperCase()}
            </div>
          )}
          <div className="min-w-0">
            <p className="break-all text-sm">{account.email}</p>
            <p className="mt-1 text-xs text-copper">{t(`auth.role.${account.role}`)}</p>
          </div>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          className="hidden"
          onChange={async (event) => {
            const file = event.target.files?.[0];
            event.target.value = "";
            if (!file) return;
            setUploading(true);
            setFailed(false);
            try {
              await uploadAvatar(file);
              await cache.invalidateQueries({ queryKey: ["auth", "me"] });
            } catch {
              setFailed(true);
            } finally {
              setUploading(false);
            }
          }}
        />
        <button
          type="button"
          disabled={uploading}
          className="mt-4 text-sm font-semibold text-copper underline disabled:opacity-50"
          onClick={() => inputRef.current?.click()}
        >
          {t(uploading ? "auth.uploading" : "auth.changePhoto")}
        </button>
        <Link
          to="/myspace/$userId"
          params={{ userId: account.id }}
          className="mt-3 block text-sm font-semibold underline"
        >
          {t("auth.myspace")}
        </Link>
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
