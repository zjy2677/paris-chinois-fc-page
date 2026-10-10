import { ImageIcon, Trash2 } from "lucide-react";
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useI18n } from "@/i18n/i18n-provider";
import { mediaUrl, useDeletePhoto, useUpdateAlbumPhoto, type Photo } from "./media-api";

type PhotoGridProps = {
  photos: Photo[];
  albumId?: string;
  canManage?: boolean;
};

export function PhotoGrid({ photos, albumId, canManage = false }: PhotoGridProps) {
  const { t } = useI18n();
  const updatePhoto = useUpdateAlbumPhoto();
  const deletePhoto = useDeletePhoto();
  if (!photos.length) return null;

  async function remove(photo: Photo) {
    if (!window.confirm(t("gallery.deletePhotoConfirm"))) return;
    await deletePhoto.mutateAsync(photo.id);
  }

  return (
    <>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-3 md:gap-4">
        {photos.map((photo, index) => (
          <div
            key={photo.id}
            className={`group relative overflow-hidden bg-muted ${index === 0 ? "col-span-2 row-span-2" : ""}`}
          >
            <Dialog>
              <DialogTrigger asChild>
                <button
                  type="button"
                  className="block h-full w-full overflow-hidden bg-muted text-left"
                  aria-label={photo.alt_text || photo.caption || t("media.photos")}
                >
                  <img
                    src={mediaUrl(photo.url)}
                    alt={photo.alt_text}
                    loading="lazy"
                    className="aspect-[4/3] h-full w-full object-cover transition duration-300 hover:scale-[1.03]"
                  />
                </button>
              </DialogTrigger>
              <DialogContent
                aria-describedby={undefined}
                className="w-[calc(100%-2rem)] max-w-6xl border-0 bg-black/90 p-10 text-white"
              >
                <DialogTitle className="sr-only">
                  {photo.alt_text || photo.caption || t("media.photos")}
                </DialogTitle>
                <figure>
                  <img
                    src={mediaUrl(photo.url)}
                    alt={photo.alt_text}
                    className="mx-auto max-h-[82vh] max-w-full object-contain"
                  />
                  {photo.caption ? (
                    <figcaption className="mt-4 text-center text-sm text-white/80">
                      {photo.caption}
                    </figcaption>
                  ) : null}
                </figure>
              </DialogContent>
            </Dialog>
            {canManage && albumId ? (
              <div className="absolute inset-x-0 bottom-0 flex items-center justify-between gap-2 bg-black/80 p-2 text-xs text-white">
                <label className="flex cursor-pointer items-center gap-2 font-semibold">
                  <input
                    type="checkbox"
                    checked={photo.use_as_background}
                    disabled={updatePhoto.isPending || deletePhoto.isPending}
                    onChange={(event) =>
                      updatePhoto.mutate({
                        albumId,
                        photoId: photo.id,
                        selected: event.target.checked,
                      })
                    }
                    className="size-4 accent-primary"
                  />
                  <ImageIcon size={15} aria-hidden="true" />
                  <span>{t("gallery.useAsBackground")}</span>
                </label>
                <button
                  type="button"
                  disabled={updatePhoto.isPending || deletePhoto.isPending}
                  onClick={() => void remove(photo)}
                  className="rounded-sm p-2 text-white transition hover:bg-white/15 disabled:opacity-60"
                  aria-label={t("gallery.deletePhoto")}
                >
                  <Trash2 size={17} aria-hidden="true" />
                </button>
              </div>
            ) : null}
          </div>
        ))}
      </div>
      {updatePhoto.isError || deletePhoto.isError ? (
        <p role="alert" className="mt-3 text-sm text-copper">
          {t("gallery.manageError")}
        </p>
      ) : null}
    </>
  );
}
