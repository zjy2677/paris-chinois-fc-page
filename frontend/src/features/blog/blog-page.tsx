import { useRef, useState } from "react";
import { useI18n } from "@/i18n/i18n-provider";
import { useAccount } from "@/features/auth/auth-api";
import { PageIntro } from "@/components/layout/page-intro";
import { assets } from "@/config/assets";
import {
  publishedPageSize,
  useBlogMutation,
  useModerationQueue,
  useMyPosts,
  usePublishedPosts,
  type BlogInput,
  type BlogPost,
  type BlogStatus,
} from "./blog-api";
import { BlogCard } from "./blog-card";
import { PhotoUploadError, uploadPhotos } from "@/features/gallery/upload-photos";

const emptyForm: BlogInput = { title: "", body: "" };

export function BlogPage() {
  const { t } = useI18n();
  const account = useAccount();
  const [publishedOffset, setPublishedOffset] = useState(0);
  const published = usePublishedPosts(publishedOffset);
  const mine = useMyPosts(Boolean(account.data));
  const moderation = useModerationQueue(account.data?.role === "admin");
  const mutation = useBlogMutation();
  const [form, setForm] = useState<BlogInput>(emptyForm);
  const [editing, setEditing] = useState<string | null>(null);
  const [photoFiles, setPhotoFiles] = useState<File[]>([]);
  const [photoError, setPhotoError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const saving = useRef(false);
  const photoInput = useRef<HTMLInputElement>(null);
  const busy = submitting || mutation.isPending;

  async function save(event: { preventDefault: () => void }, submit: boolean) {
    event.preventDefault();
    if (saving.current || mutation.isPending) return;
    saving.current = true;
    setSubmitting(true);
    setPhotoError(null);
    try {
      const post = await mutation.mutateAsync({
        path: editing ? `/posts/${editing}` : "/posts",
        method: editing ? "PATCH" : "POST",
        body: editing ? form : { ...form, submit: false },
      });
      // Keep the draft ID if uploading or review submission fails.
      setEditing(post.id);
      await uploadPhotos(
        `/blog/${post.id}/photos`,
        photoFiles,
        () => setPhotoFiles((remaining) => remaining.slice(1)),
        { alt: form.title },
      );
      if (photoInput.current) photoInput.current.value = "";
      if (submit) await mutation.mutateAsync({ path: `/posts/${post.id}/submit` });
      setForm(emptyForm);
      setEditing(null);
    } catch (error) {
      if (error instanceof PhotoUploadError) setPhotoError(error.fileName);
      // Other failures are exposed by the mutation state below.
    } finally {
      await mine.refetch();
      saving.current = false;
      setSubmitting(false);
    }
  }

  function edit(post: BlogPost) {
    if (saving.current) return;
    setEditing(post.id);
    setForm({ title: post.title, body: post.body });
    setPhotoFiles([]);
    setPhotoError(null);
    if (photoInput.current) photoInput.current.value = "";
    document.querySelector("#blog-editor")?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <>
      <PageIntro
        backgroundImage={assets.match}
        eyebrow={t("blog.eyebrow")}
        title={t("blog.title")}
        description={t("blog.intro")}
      />
      <div className="site-container py-14 md:py-20">
        {published.isPending ? <p>{t("blog.loading")}</p> : null}
        {published.isError ? <p className="text-copper">{t("blog.error")}</p> : null}
        {published.data?.items.length === 0 ? (
          <p className="border border-border bg-card p-8 text-muted-foreground">
            {t("blog.empty")}
          </p>
        ) : null}
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {published.data?.items.map((post) => (
            <BlogCard key={post.id} post={post} />
          ))}
        </div>

        {published.data && (published.data.total > publishedPageSize || publishedOffset > 0) ? (
          <nav
            className="mt-8 flex items-center justify-between gap-4"
            aria-label={t("blog.pagination")}
          >
            <button
              type="button"
              disabled={publishedOffset === 0 || published.isFetching}
              onClick={() =>
                setPublishedOffset((offset) => Math.max(0, offset - publishedPageSize))
              }
              className="border border-border px-4 py-3 text-sm disabled:opacity-40"
            >
              {t("blog.previous")}
            </button>
            <button
              type="button"
              disabled={
                publishedOffset + publishedPageSize >= published.data.total ||
                published.isFetching ||
                published.isError
              }
              onClick={() => setPublishedOffset((offset) => offset + publishedPageSize)}
              className="border border-border px-4 py-3 text-sm disabled:opacity-40"
            >
              {t("blog.next")}
            </button>
          </nav>
        ) : null}

        <section id="blog-editor" className="mt-20 border-t border-border pt-14">
          <p className="eyebrow text-primary">{t("blog.contribute")}</p>
          <h2 className="mt-4 font-display text-5xl font-bold uppercase">{t("blog.shareStory")}</h2>
          {!account.data ? (
            <p className="mt-5 max-w-xl text-muted-foreground">{t("blog.loginRequired")}</p>
          ) : (
            <form className="mt-8 max-w-3xl space-y-5" onSubmit={(event) => save(event, false)}>
              <Field label={t("blog.postTitle")}>
                <input
                  required
                  disabled={busy}
                  minLength={3}
                  maxLength={180}
                  value={form.title}
                  onChange={(event) => setForm({ ...form, title: event.target.value })}
                  className="w-full border border-border bg-card px-4 py-3"
                />
              </Field>
              <Field label={t("media.addPhotos")}>
                <input
                  ref={photoInput}
                  disabled={busy}
                  type="file"
                  multiple
                  accept="image/png,image/jpeg,image/webp"
                  onChange={(event) =>
                    setPhotoFiles(Array.from(event.target.files ?? []).slice(0, 20))
                  }
                  className="w-full border border-border bg-card px-4 py-3"
                />
                <span className="block font-normal text-muted-foreground">
                  {t("media.photoHelp")}
                </span>
              </Field>
              <Field label={t("blog.body")}>
                <textarea
                  required
                  disabled={busy}
                  minLength={20}
                  maxLength={20000}
                  rows={12}
                  value={form.body}
                  onChange={(event) => setForm({ ...form, body: event.target.value })}
                  className="w-full resize-y border border-border bg-card px-4 py-3 leading-7"
                />
              </Field>
              <div className="flex flex-wrap gap-3">
                <button disabled={busy} className="bg-secondary px-5 py-3 text-sm font-bold">
                  {editing ? t("blog.saveChanges") : t("blog.saveDraft")}
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={(event) => save(event, true)}
                  className="bg-primary px-5 py-3 text-sm font-bold"
                >
                  {t("blog.submitReview")}
                </button>
                {editing ? (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => {
                      setEditing(null);
                      setForm(emptyForm);
                      setPhotoFiles([]);
                      setPhotoError(null);
                      if (photoInput.current) photoInput.current.value = "";
                    }}
                    className="px-5 py-3 text-sm underline"
                  >
                    {t("blog.cancelEdit")}
                  </button>
                ) : null}
              </div>
              {mutation.isError ? <p className="text-copper">{t("blog.saveError")}</p> : null}
              {photoError ? (
                <p role="alert" className="text-copper">
                  {t("media.uploadError")} {photoError}
                </p>
              ) : null}
            </form>
          )}
        </section>

        {account.data ? (
          <PostManager
            title={t("blog.myPosts")}
            posts={mine.data ?? []}
            t={t}
            onEdit={edit}
            onAction={(post, action) => mutation.mutate({ path: `/posts/${post.id}/${action}` })}
            admin={false}
            disabled={busy}
          />
        ) : null}
        {account.data?.role === "admin" ? (
          <PostManager
            title={t("blog.moderation")}
            posts={moderation.data ?? []}
            t={t}
            onEdit={edit}
            onAction={(post, action) => mutation.mutate({ path: `/posts/${post.id}/${action}` })}
            admin
            disabled={busy}
          />
        ) : null}
      </div>
    </>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-2 text-sm font-bold">
      <span>{label}</span>
      {children}
    </label>
  );
}

function PostManager({
  title,
  posts,
  t,
  onEdit,
  onAction,
  admin,
  disabled,
}: {
  title: string;
  posts: BlogPost[];
  t: ReturnType<typeof useI18n>["t"];
  onEdit: (post: BlogPost) => void;
  onAction: (post: BlogPost, action: "submit" | "publish" | "reject") => void;
  admin: boolean;
  disabled: boolean;
}) {
  return (
    <section className="mt-16 border-t border-border pt-12">
      <h2 className="font-display text-4xl font-bold uppercase">{title}</h2>
      {posts.length === 0 ? <p className="mt-5 text-muted-foreground">{t("blog.none")}</p> : null}
      <div className="mt-6 space-y-4">
        {posts.map((post) => (
          <article key={post.id} className="border border-border bg-card p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h3 className="text-lg font-bold">{post.title}</h3>
                <p className="mt-1 text-sm text-copper">
                  {t(`blog.status.${post.status}` as `blog.status.${BlogStatus}`)}
                </p>
              </div>
              <div className="flex gap-4 text-sm">
                {admin ? (
                  <>
                    <button
                      disabled={disabled}
                      onClick={() => onAction(post, "publish")}
                      className="underline"
                    >
                      {t("blog.publish")}
                    </button>
                    <button
                      disabled={disabled}
                      onClick={() => onAction(post, "reject")}
                      className="underline"
                    >
                      {t("blog.reject")}
                    </button>
                  </>
                ) : null}
                {!admin && ["draft", "rejected"].includes(post.status) ? (
                  <>
                    <button disabled={disabled} onClick={() => onEdit(post)} className="underline">
                      {t("blog.edit")}
                    </button>
                    <button
                      disabled={disabled}
                      onClick={() => onAction(post, "submit")}
                      className="underline"
                    >
                      {t("blog.submitReview")}
                    </button>
                  </>
                ) : null}
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
