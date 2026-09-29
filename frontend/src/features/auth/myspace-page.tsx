import { useI18n } from "@/i18n/i18n-provider";
import { Link, useParams } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { avatarUrl, uploadAvatar, useAccount } from "./auth-api";

export function MyspacePage() {
  const { t } = useI18n();
  const account = useAccount();
  const cache = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(false);
  const { userId } = useParams({ from: "/myspace/$userId" });
  const ownPage = account.data?.id === userId;

  if (account.isLoading) return <section className="site-container py-32">{t("auth.loading")}</section>;
  if (!account.data) {
    return (
      <section className="site-container py-32">
        <h1 className="font-display text-5xl font-bold uppercase">{t("auth.myspace")}</h1>
        <p className="mt-4 text-muted-foreground">{t("auth.loginForMyspace")}</p>
      </section>
    );
  }
  if (!ownPage) {
    return (
      <section className="site-container py-32">
        <h1 className="font-display text-5xl font-bold uppercase">{t("auth.privateProfile")}</h1>
        <Link to="/myspace/$userId" params={{ userId: account.data.id }} className="mt-5 inline-block underline">
          {t("auth.myspace")}
        </Link>
      </section>
    );
  }
  const photo = avatarUrl(account.data);
  return (
    <section className="site-container py-32">
      <p className="eyebrow text-copper">{t("auth.account")}</p>
      <h1 className="mt-3 font-display text-6xl font-bold uppercase">{t("auth.myspace")}</h1>
      <div className="mt-10 flex max-w-xl items-center gap-5 border border-border bg-card p-6">
        {photo ? <img src={photo} alt="" className="h-24 w-24 rounded-full object-cover" /> : <div className="h-24 w-24 rounded-full bg-secondary" />}
        <div className="min-w-0">
          <p className="break-all font-semibold">{account.data.email}</p>
          <p className="mt-2 text-sm text-muted-foreground">{t(`auth.role.${account.data.role}`)}</p>
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
              setUploadError(false);
              try {
                await uploadAvatar(file);
                await cache.invalidateQueries({ queryKey: ["auth", "me"] });
              } catch {
                setUploadError(true);
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
          {uploadError && <p role="alert" className="mt-2 text-sm text-copper">{t("auth.uploadError")}</p>}
        </div>
      </div>
    </section>
  );
}
