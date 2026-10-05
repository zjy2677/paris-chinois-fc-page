import { useState, type FormEvent } from "react";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useI18n } from "@/i18n/i18n-provider";
import { ApiError, useAddMatchVideo, useDeleteMatchVideo, type Highlight } from "./league-api";

export function HighlightEditor({ matchId, videos }: { matchId: string; videos: Highlight[] }) {
  const { t } = useI18n();
  const addVideo = useAddMatchVideo(matchId);
  const deleteVideo = useDeleteMatchVideo(matchId);
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const trimmedUrl = url.trim();
    if (!trimmedUrl) return;
    addVideo.mutate(
      { url: trimmedUrl, title: title.trim() || null },
      {
        onSuccess: () => {
          setUrl("");
          setTitle("");
        },
      },
    );
  };

  const errorKey =
    addVideo.error instanceof ApiError
      ? addVideo.error.status === 409
        ? "match.videoDuplicate"
        : addVideo.error.status === 422
          ? "match.videoInvalid"
          : "match.videoAddError"
      : "match.videoAddError";

  return (
    <div className="mt-6 border border-border bg-card p-5 md:p-6">
      <h3 className="font-display text-2xl font-bold uppercase">{t("match.addVideo")}</h3>
      <form
        className="mt-4 grid gap-3 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_auto]"
        onSubmit={submit}
      >
        <label className="text-sm font-medium">
          {t("match.youtubeUrl")}
          <Input
            className="mt-2"
            type="url"
            inputMode="url"
            required
            placeholder="https://www.youtube.com/watch?v=…"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
          />
        </label>
        <label className="text-sm font-medium">
          {t("match.videoTitle")}
          <Input
            className="mt-2"
            maxLength={200}
            placeholder={t("match.videoTitleOptional")}
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
        </label>
        <Button className="self-end" type="submit" disabled={addVideo.isPending || !url.trim()}>
          <Plus aria-hidden="true" />
          {addVideo.isPending ? t("auth.pending") : t("match.addVideo")}
        </Button>
      </form>
      <p className="mt-3 text-sm text-muted-foreground">{t("match.youtubeHint")}</p>
      {addVideo.isError && (
        <p className="mt-3 text-sm text-destructive" role="alert">
          {t(errorKey)}
        </p>
      )}
      {deleteVideo.isError && (
        <p className="mt-3 text-sm text-destructive" role="alert">
          {t("match.videoDeleteError")}
        </p>
      )}
      {videos.length > 0 && (
        <ul className="mt-5 divide-y divide-border border-t border-border">
          {videos.map((video, index) => (
            <li key={video.id} className="flex items-center justify-between gap-4 py-3">
              <span className="min-w-0 truncate text-sm">
                {video.title || `${t("match.highlights")} ${index + 1}`}
              </span>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                disabled={deleteVideo.isPending}
                onClick={() => {
                  if (window.confirm(t("match.videoDeleteConfirm"))) deleteVideo.mutate(video.id);
                }}
              >
                <Trash2 aria-hidden="true" />
                {t("match.deleteVideo")}
              </Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
