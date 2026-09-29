import { useI18n } from "@/i18n/i18n-provider";
import type { GuestbookMessage } from "./guestbook-api";

const accents = ["border-t-primary", "border-t-copper", "border-t-foreground/60"] as const;

export function MessageCard({
  message,
  index,
  adminAction,
}: {
  message: GuestbookMessage;
  index: number;
  adminAction?: () => void;
}) {
  const { t, formatDate } = useI18n();
  return (
    <article
      className={`mb-5 break-inside-avoid border border-border border-t-4 bg-card p-6 shadow-[0_12px_35px_rgba(0,0,0,.16)] ${accents[index % accents.length]} ${message.status === "hidden" ? "opacity-55" : ""}`}
    >
      <div className="flex items-start justify-between gap-4">
        <h2 className="font-display text-2xl font-bold uppercase">{message.nickname}</h2>
        {message.status === "hidden" ? (
          <span className="text-xs uppercase text-muted-foreground">{t("guestbook.hidden")}</span>
        ) : null}
      </div>
      <p className="mt-5 whitespace-pre-wrap text-[15px] leading-7 text-foreground/90">
        {message.body}
      </p>
      <div className="mt-6 flex items-end justify-between gap-4 border-t border-border pt-4">
        <time className="text-xs text-muted-foreground">
          {formatDate(message.created_at, { day: "numeric", month: "long", year: "numeric" })}
        </time>
        {adminAction ? (
          <button type="button" onClick={adminAction} className="text-xs text-copper underline">
            {message.status === "hidden" ? t("guestbook.restore") : t("guestbook.hide")}
          </button>
        ) : null}
      </div>
    </article>
  );
}
