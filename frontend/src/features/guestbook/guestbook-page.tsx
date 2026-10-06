import { useState, type FormEvent } from "react";
import { PageIntro } from "@/components/layout/page-intro";
import { useAccount } from "@/features/auth/auth-api";
import { assets } from "@/config/assets";
import { useI18n } from "@/i18n/i18n-provider";
import {
  useGuestbookMessages,
  useGuestbookModeration,
  useGuestbookMutation,
} from "./guestbook-api";
import { MessageCard } from "./message-card";
import { uploadPhoto } from "@/features/gallery/media-api";

export function GuestbookPage() {
  const { t } = useI18n();
  const account = useAccount();
  const messages = useGuestbookMessages();
  const moderation = useGuestbookModeration(account.data?.role === "admin");
  const mutation = useGuestbookMutation();
  const moderate = useGuestbookMutation();
  const [nickname, setNickname] = useState("");
  const [body, setBody] = useState("");
  const [published, setPublished] = useState(false);
  const [photo, setPhoto] = useState<File | null>(null);
  const [awaitingReview, setAwaitingReview] = useState(false);

  function submit(event: FormEvent) {
    event.preventDefault();
    setPublished(false);
    setAwaitingReview(false);
    mutation.mutate(
      { path: "/messages", body: { nickname, body } },
      {
        onSuccess: async (message) => {
          if (photo) {
            try {
              await uploadPhoto(`/guestbook/${message.id}/photo`, photo, {
                alt: `${nickname} guestbook photo`,
              });
              setAwaitingReview(true);
            } catch {
              // The text message remains published if its optional photo fails.
            }
          }
          setNickname("");
          setBody("");
          setPhoto(null);
          setPublished(true);
        },
      },
    );
  }

  const hidden = moderation.data?.filter((message) => message.status === "hidden") ?? [];

  return (
    <>
      <PageIntro
        backgroundImage={assets.contact}
        eyebrow={t("guestbook.eyebrow")}
        title={t("guestbook.title")}
        description={t("guestbook.intro")}
      />
      <div className="site-container py-14 md:py-20">
        <section className="grid gap-10 border-b border-border pb-16 lg:grid-cols-[.7fr_1.3fr]">
          <div>
            <p className="eyebrow text-primary">{t("guestbook.leaveNote")}</p>
            <h2 className="mt-4 font-display text-5xl font-bold uppercase md:text-6xl">
              {t("guestbook.saySomething")}
            </h2>
            <p className="mt-5 max-w-md text-sm leading-6 text-muted-foreground">
              {t("guestbook.guidance")}
            </p>
          </div>
          <form onSubmit={submit} className="space-y-5 border border-border bg-card p-6 md:p-8">
            <label className="block space-y-2 text-sm font-bold">
              <span>{t("guestbook.nickname")}</span>
              <input
                required
                maxLength={30}
                value={nickname}
                onChange={(event) => setNickname(event.target.value)}
                className="w-full border border-border bg-background px-4 py-3"
              />
            </label>
            <label className="block space-y-2 text-sm font-bold">
              <span>{t("media.addPhotos")}</span>
              <input
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={(event) => setPhoto(event.target.files?.[0] ?? null)}
                className="w-full border border-border bg-background px-4 py-3"
              />
              <span className="block font-normal text-muted-foreground">
                {t("media.photoHelp")}
              </span>
            </label>
            <label className="block space-y-2 text-sm font-bold">
              <span>{t("guestbook.message")}</span>
              <textarea
                required
                minLength={2}
                maxLength={300}
                rows={5}
                value={body}
                onChange={(event) => setBody(event.target.value)}
                className="w-full resize-y border border-border bg-background px-4 py-3 leading-7"
              />
            </label>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <span className="text-xs tabular-nums text-muted-foreground">
                {body.length} / 300
              </span>
              <button
                disabled={mutation.isPending}
                className="bg-primary px-6 py-3 text-sm font-bold disabled:opacity-50"
              >
                {mutation.isPending ? t("guestbook.posting") : t("guestbook.post")}
              </button>
            </div>
            {published && !awaitingReview ? (
              <p className="text-sm text-copper">{t("guestbook.success")}</p>
            ) : null}
            {awaitingReview ? (
              <p className="text-sm text-copper">{t("media.pendingModeration")}</p>
            ) : null}
            {mutation.isError ? (
              <p className="text-sm text-copper">{t("guestbook.error")}</p>
            ) : null}
          </form>
        </section>

        {moderate.isError ? (
          <p role="alert" className="mt-8 text-sm text-copper">
            {t("guestbook.moderationError")}
          </p>
        ) : null}

        <section className="pt-16" aria-labelledby="message-wall-title">
          <p className="eyebrow text-copper">{t("guestbook.community")}</p>
          <h2 id="message-wall-title" className="mt-4 font-display text-5xl font-bold uppercase">
            {t("guestbook.wall")}
          </h2>
          {messages.isPending ? <p className="mt-8">{t("guestbook.loading")}</p> : null}
          {messages.isError ? <p className="mt-8 text-copper">{t("guestbook.loadError")}</p> : null}
          {messages.data?.length === 0 ? (
            <p className="mt-8 border border-border bg-card p-8 text-muted-foreground">
              {t("guestbook.empty")}
            </p>
          ) : null}
          <div className="mt-8 columns-1 gap-5 md:columns-2 xl:columns-3">
            {messages.data?.map((message, index) => (
              <MessageCard
                key={message.id}
                message={message}
                index={index}
                {...(account.data?.role === "admin"
                  ? {
                      adminPending: moderate.isPending,
                      adminAction: () => moderate.mutate({ path: `/messages/${message.id}/hide` }),
                    }
                  : {})}
              />
            ))}
          </div>
        </section>

        {account.data?.role === "admin" && hidden.length > 0 ? (
          <section className="mt-16 border-t border-border pt-12">
            <h2 className="font-display text-4xl font-bold uppercase">
              {t("guestbook.hiddenMessages")}
            </h2>
            <div className="mt-8 columns-1 gap-5 md:columns-2 xl:columns-3">
              {hidden.map((message, index) => (
                <MessageCard
                  key={message.id}
                  message={message}
                  index={index}
                  adminPending={moderate.isPending}
                  adminAction={() => moderate.mutate({ path: `/messages/${message.id}/restore` })}
                />
              ))}
            </div>
          </section>
        ) : null}
      </div>
    </>
  );
}
