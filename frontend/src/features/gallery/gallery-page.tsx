import { useRef, useState, type FormEvent } from "react";
import { Images } from "lucide-react";
import { PageIntro } from "@/components/layout/page-intro";
import { assets } from "@/config/assets";
import { useAccount } from "@/features/auth/auth-api";
import { useI18n } from "@/i18n/i18n-provider";
import { AlbumAdminControls } from "./album-admin-controls";
import { PhotoGrid } from "./photo-grid";
import { useAlbums, useCreateAlbum } from "./media-api";
import { PhotoUploadError, uploadPhotos } from "./upload-photos";

export function GalleryPage() {
  const { t, formatDate } = useI18n();
  const account = useAccount();
  const albums = useAlbums();
  const create = useCreateAlbum();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [date, setDate] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [retryAlbumId, setRetryAlbumId] = useState<string | null>(null);
  const [photoError, setPhotoError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const submitting = useRef(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (submitting.current || !files.length) return;
    submitting.current = true;
    setUploading(true);
    setPhotoError(null);
    try {
      let albumId = retryAlbumId;
      if (!albumId) {
        const album = await create.mutateAsync({
          title,
          description: description || null,
          event_date: date ? new Date(date).toISOString() : null,
        });
        albumId = album.id;
        setRetryAlbumId(album.id);
      }
      await uploadPhotos(
        `/albums/${albumId}/photos`,
        files,
        () => setFiles((remaining) => remaining.slice(1)),
        { alt: title },
      );
      setTitle("");
      setDescription("");
      setDate("");
      setRetryAlbumId(null);
      if (fileInput.current) fileInput.current.value = "";
    } catch (error) {
      if (error instanceof PhotoUploadError) setPhotoError(error.fileName);
      // Album creation errors are exposed by the mutation below.
    } finally {
      await albums.refetch();
      submitting.current = false;
      setUploading(false);
    }
  }

  return (
    <>
      <PageIntro
        backgroundImage={assets.training}
        eyebrow={t("gallery.eyebrow")}
        title={t("gallery.title")}
        description={t("gallery.intro")}
      />
      <div className="site-container py-14 md:py-20">
        {account.data?.role === "admin" ? (
          <form
            onSubmit={submit}
            className="mb-16 grid gap-4 border border-border bg-card p-6 md:grid-cols-2"
          >
            <h2 className="font-display text-4xl font-bold uppercase md:col-span-2">
              {t("gallery.create")}
            </h2>
            <input
              required
              disabled={uploading || retryAlbumId !== null}
              minLength={2}
              maxLength={180}
              placeholder={t("gallery.albumTitle")}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="border border-border bg-background px-4 py-3"
            />
            <input
              type="date"
              disabled={uploading || retryAlbumId !== null}
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="border border-border bg-background px-4 py-3"
            />
            <textarea
              disabled={uploading || retryAlbumId !== null}
              maxLength={2000}
              placeholder={t("gallery.description")}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="border border-border bg-background px-4 py-3 md:col-span-2"
            />
            <input
              required
              ref={fileInput}
              disabled={uploading}
              multiple
              accept="image/png,image/jpeg,image/webp"
              type="file"
              onChange={(e) => setFiles(Array.from(e.target.files ?? []).slice(0, 20))}
              className="md:col-span-2"
            />
            <button
              disabled={uploading || !files.length}
              className="bg-primary px-5 py-3 font-bold md:w-fit"
            >
              {uploading
                ? t("gallery.uploading")
                : retryAlbumId
                  ? t("media.retryUpload")
                  : t("gallery.publish")}
            </button>
            {create.isError ? (
              <p role="alert" className="text-copper md:col-span-2">
                {t("blog.saveError")}
              </p>
            ) : null}
            {photoError ? (
              <p role="alert" className="text-copper md:col-span-2">
                {t("media.uploadError")} {photoError}
              </p>
            ) : null}
          </form>
        ) : null}
        {albums.isPending ? <p>{t("gallery.loading")}</p> : null}
        {albums.data?.length === 0 ? (
          <div className="flex min-h-64 flex-col items-center justify-center border border-border bg-card">
            <Images className="text-copper" />
            <p className="mt-4 text-muted-foreground">{t("gallery.empty")}</p>
          </div>
        ) : null}
        <div className="space-y-20">
          {albums.data?.map((album) => (
            <article key={album.id}>
              <p className="eyebrow text-copper">
                {album.event_date
                  ? formatDate(album.event_date, { day: "numeric", month: "long", year: "numeric" })
                  : t("gallery.album")}
              </p>
              <h2 className="mt-3 font-display text-5xl font-bold uppercase">{album.title}</h2>
              {album.description ? (
                <p className="mb-7 mt-3 max-w-2xl text-muted-foreground">{album.description}</p>
              ) : (
                <div className="mb-7" />
              )}
              {account.data?.role === "admin" ? (
                <AlbumAdminControls
                  album={album}
                  onDeleted={(deletedId) =>
                    setRetryAlbumId((current) => (current === deletedId ? null : current))
                  }
                />
              ) : null}
              <PhotoGrid
                photos={album.photos}
                albumId={album.id}
                canManage={account.data?.role === "admin"}
              />
            </article>
          ))}
        </div>
      </div>
    </>
  );
}
