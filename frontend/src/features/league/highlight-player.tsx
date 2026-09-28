import { useState } from "react";
import { Play, RotateCcw } from "lucide-react";
import { useI18n } from "@/i18n/i18n-provider";

export function HighlightPlayer({ embedUrl, title }: { embedUrl: string; title: string }) {
  const { t } = useI18n();
  const [attempt, setAttempt] = useState(0);
  const [started, setStarted] = useState(false);
  const [thumbnail, setThumbnail] = useState("maxresdefault.jpg");
  const url = new URL(embedUrl);
  // The API supplies validated YouTube embed URLs. Keep iframe destinations explicit.
  const id = url.pathname.match(/^\/embed\/([A-Za-z0-9_-]{11})$/)?.[1];
  if (!id || !["www.youtube.com", "www.youtube-nocookie.com"].includes(url.hostname)) return null;
  const host = attempt % 2 === 0 ? "www.youtube.com" : "www.youtube-nocookie.com";
  const src = `https://${host}/embed/${id}?playsinline=1&rel=0&autoplay=1`;
  return (
    <div>
      <div className="relative aspect-video min-h-[200px] w-full overflow-hidden border border-border bg-black">
        {started ? (
          <iframe
            key={attempt}
            src={src}
            title={title}
            width="1280"
            height="720"
            className="absolute inset-0 h-full w-full"
            referrerPolicy="strict-origin-when-cross-origin"
            allow="autoplay; encrypted-media; picture-in-picture; fullscreen"
            allowFullScreen
          />
        ) : (
          <button
            type="button"
            onClick={() => setStarted(true)}
            aria-label={t("match.playHighlights")}
            className="absolute inset-0 flex h-full w-full items-center justify-center focus-visible:outline focus-visible:outline-2 focus-visible:outline-copper"
          >
            <img
              src={`https://i.ytimg.com/vi/${id}/${thumbnail}`}
              onError={() => {
                if (thumbnail !== "hqdefault.jpg") setThumbnail("hqdefault.jpg");
              }}
              alt=""
              className="absolute inset-0 h-full w-full object-cover opacity-70"
            />
            <span className="relative flex items-center gap-3 bg-primary px-6 py-4 font-semibold text-white shadow-lg">
              <Play aria-hidden="true" size={24} />
              {t("match.playHighlights")}
            </span>
          </button>
        )}
      </div>
      {started && (
        <button
          type="button"
          onClick={() => setAttempt((value) => value + 1)}
          className="mt-3 inline-flex items-center gap-2 py-2 text-sm text-copper underline-offset-4 hover:underline"
        >
          <RotateCcw size={16} aria-hidden="true" />
          {t("match.retryVideo")}
        </button>
      )}
    </div>
  );
}
