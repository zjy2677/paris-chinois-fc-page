import { useState } from "react";

export function PlayerPortrait({
  name,
  photoUrl,
  number,
}: {
  name: string;
  photoUrl: string | null;
  number: number | null;
}) {
  const [failedPhoto, setFailedPhoto] = useState<string | null>(null);
  const photo = photoUrl && photoUrl !== failedPhoto ? photoUrl : null;
  return (
    <div className="relative flex aspect-[4/4.5] items-end justify-center overflow-hidden bg-secondary">
      <div className="texture absolute inset-0 opacity-70" />
      {number !== null && (
        <div className="absolute left-4 top-4 z-10 font-display text-5xl font-bold text-copper drop-shadow-lg">
          {String(number).padStart(2, "0")}
        </div>
      )}
      {photo ? (
        <img
          src={photo}
          alt={name}
          loading="lazy"
          referrerPolicy="no-referrer"
          onError={() => setFailedPhoto(photo)}
          className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
        />
      ) : (
        <svg
          aria-hidden="true"
          viewBox="0 0 300 330"
          className="relative h-[85%] w-[85%] translate-y-8 fill-muted-foreground/20"
        >
          <circle cx="150" cy="100" r="48" />
          <path d="M70 250c0-56 28-93 80-93s80 37 80 93v100H70z" />
        </svg>
      )}
    </div>
  );
}
