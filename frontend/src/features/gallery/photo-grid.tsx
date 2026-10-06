import { useState } from "react";
import { X } from "lucide-react";
import { mediaUrl, type Photo } from "./media-api";

export function PhotoGrid({ photos }: { photos: Photo[] }) {
  const [active, setActive] = useState<Photo | null>(null);
  if (!photos.length) return null;
  return (
    <>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-3 md:gap-4">
        {photos.map((photo, index) => (
          <button
            key={photo.id}
            type="button"
            className={`overflow-hidden bg-muted text-left ${index === 0 ? "col-span-2 row-span-2" : ""}`}
            onClick={() => setActive(photo)}
          >
            <img
              src={mediaUrl(photo.url)}
              alt={photo.alt_text}
              loading="lazy"
              className="aspect-[4/3] h-full w-full object-cover transition duration-300 hover:scale-[1.03]"
            />
          </button>
        ))}
      </div>
      {active ? (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4 md:p-10"
          onClick={() => setActive(null)}
        >
          <button
            className="absolute right-5 top-5 text-white"
            aria-label="Close"
            onClick={() => setActive(null)}
          >
            <X size={32} />
          </button>
          <figure className="max-h-full max-w-6xl" onClick={(event) => event.stopPropagation()}>
            <img
              src={mediaUrl(active.url)}
              alt={active.alt_text}
              className="max-h-[82vh] max-w-full object-contain"
            />
            {active.caption ? (
              <figcaption className="mt-4 text-center text-sm text-white/80">
                {active.caption}
              </figcaption>
            ) : null}
          </figure>
        </div>
      ) : null}
    </>
  );
}
