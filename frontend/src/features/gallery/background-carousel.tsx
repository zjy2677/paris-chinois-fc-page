import { useEffect, useState } from "react";
import { mediaUrl, useBackgrounds, type BackgroundTransition } from "./media-api";

type BackgroundCarouselProps = {
  fallback: string;
  className?: string;
  fallbackImageClassName?: string;
  imageClassName?: string;
  priority?: boolean;
};

function transitionClass(transition: BackgroundTransition, active: boolean) {
  if (transition === "slide") {
    return active ? "translate-x-0 opacity-100" : "translate-x-[4%] opacity-0";
  }
  if (transition === "zoom") {
    return active ? "scale-100 opacity-100" : "scale-105 opacity-0";
  }
  return active ? "opacity-100" : "opacity-0";
}

export function BackgroundCarousel({
  fallback,
  className = "",
  fallbackImageClassName = "",
  imageClassName = "object-center",
  priority = false,
}: BackgroundCarouselProps) {
  const backgrounds = useBackgrounds();
  const [activeIndex, setActiveIndex] = useState(0);
  const photos = backgrounds.data?.photos ?? [];
  const intervalSeconds = backgrounds.data?.interval_seconds ?? 8;
  const transition = backgrounds.data?.transition ?? "fade";

  useEffect(() => setActiveIndex(0), [photos.length]);

  useEffect(() => {
    if (photos.length < 2) return;
    const timer = window.setInterval(
      () => setActiveIndex((current) => (current + 1) % photos.length),
      intervalSeconds * 1000,
    );
    return () => window.clearInterval(timer);
  }, [intervalSeconds, photos.length]);

  return (
    <div className={`absolute inset-0 ${className}`} aria-hidden="true">
      <img
        src={fallback}
        alt=""
        fetchPriority={priority ? "high" : "auto"}
        className={`absolute inset-0 h-full w-full object-cover ${imageClassName} ${fallbackImageClassName}`}
      />
      {photos.map((photo, index) => (
        <img
          key={photo.id}
          src={mediaUrl(photo.url)}
          alt=""
          fetchPriority={priority && index === 0 ? "high" : "auto"}
          loading={priority && index === 0 ? "eager" : "lazy"}
          className={`absolute inset-0 h-full w-full object-cover transition-[opacity,transform] duration-1000 ease-in-out motion-reduce:transition-none ${imageClassName} ${transitionClass(transition, index === activeIndex)}`}
        />
      ))}
    </div>
  );
}
