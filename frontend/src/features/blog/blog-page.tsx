import { useState } from "react";
import { useI18n } from "@/i18n/i18n-provider";
import { useAccount } from "@/features/auth/auth-api";
import { PageIntro } from "@/components/layout/page-intro";
import { assets } from "@/config/assets";
import {
  useBlogMutation,
  useModerationQueue,
  useMyPosts,
  usePublishedPosts,
  type BlogInput,
  type BlogPost,
  type BlogStatus,
} from "./blog-api";
import { BlogCard } from "./blog-card";

const emptyForm: BlogInput = { title: "", body: "" };

export function BlogPage() {
  const { t } = useI18n();
  const account = useAccount();
  const published = usePublishedPosts();
  const mine = useMyPosts(Boolean(account.data));
  const moderation = useModerationQueue(account.data?.role === "admin");
  const mutation = useBlogMutation();
  const [form, setForm] = useState<BlogInput>(emptyForm);
  const [editing, setEditing] = useState<string | null>(null);

  function save(event: { preventDefault: () => void }, submit: boolean) {
    event.preventDefault();
    const path = editing ? `/posts/${editing}` : "/posts";
    mutation.mutate(
      {
        path,
        method: editing ? "PATCH" : "POST",
        body: editing ? form : { ...form, submit },
      },
      {
        onSuccess: (post) => {
          if (editing && submit) {
            mutation.mutate({ path: `/posts/${post.id}/submit` });
          }
          setForm(emptyForm);
          setEditing(null);
        },
      },
    );
  }

  function edit(post: BlogPost) {
    setEditing(post.id);
    setForm({ title: post.title, body: post.body });
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
                  minLength={3}
                  maxLength={180}
                  value={form.title}
                  onChange={(event) => setForm({ ...form, title: event.target.value })}
                  className="w-full border border-border bg-card px-4 py-3"
                />
              </Field>
              <Field label={t("blog.body")}>
                <textarea
                  required
                  minLength={20}
                  maxLength={20000}
                  rows={12}
                  value={form.body}
                  onChange={(event) => setForm({ ...form, body: event.target.value })}
                  className="w-full resize-y border border-border bg-card px-4 py-3 leading-7"
                />
              </Field>
              <div className="flex flex-wrap gap-3">
                <button
                  disabled={mutation.isPending}
                  className="bg-secondary px-5 py-3 text-sm font-bold"
                >
                  {editing ? t("blog.saveChanges") : t("blog.saveDraft")}
                </button>
                <button
                  type="button"
                  disabled={mutation.isPending}
                  onClick={(event) => save(event, true)}
                  className="bg-primary px-5 py-3 text-sm font-bold"
                >
                  {t("blog.submitReview")}
                </button>
                {editing ? (
                  <button
                    type="button"
                    onClick={() => {
                      setEditing(null);
                      setForm(emptyForm);
                    }}
                    className="px-5 py-3 text-sm underline"
                  >
                    {t("blog.cancelEdit")}
                  </button>
                ) : null}
              </div>
              {mutation.isError ? <p className="text-copper">{t("blog.saveError")}</p> : null}
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
}: {
  title: string;
  posts: BlogPost[];
  t: ReturnType<typeof useI18n>["t"];
  onEdit: (post: BlogPost) => void;
  onAction: (post: BlogPost, action: "submit" | "publish" | "reject") => void;
  admin: boolean;
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
                    <button onClick={() => onAction(post, "publish")} className="underline">
                      {t("blog.publish")}
                    </button>
                    <button onClick={() => onAction(post, "reject")} className="underline">
                      {t("blog.reject")}
                    </button>
                  </>
                ) : null}
                {!admin && ["draft", "rejected"].includes(post.status) ? (
                  <>
                    <button onClick={() => onEdit(post)} className="underline">
                      {t("blog.edit")}
                    </button>
                    <button onClick={() => onAction(post, "submit")} className="underline">
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
