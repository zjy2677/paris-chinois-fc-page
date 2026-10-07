import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useI18n } from "@/i18n/i18n-provider";
import { mediaUrl, type Photo } from "./media-api";

export function PhotoGrid({ photos }: { photos: Photo[] }) {
  const { t } = useI18n();
  if (!photos.length) return null;
  return (
    <>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-3 md:gap-4">
        {photos.map((photo, index) => (
          <Dialog key={photo.id}>
            <DialogTrigger asChild>
              <button
                type="button"
                className={`overflow-hidden bg-muted text-left ${index === 0 ? "col-span-2 row-span-2" : ""}`}
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
        ))}
      </div>
    </>
  );
}
