import { useEffect, useState, type FormEvent } from "react";
import { Settings2, Trash2 } from "lucide-react";
import { useI18n } from "@/i18n/i18n-provider";
import { useDeleteAlbum, useUpdateAlbum, type Album, type BackgroundTransition } from "./media-api";

export function AlbumAdminControls({ album }: { album: Album }) {
  const { t } = useI18n();
  const updateAlbum = useUpdateAlbum();
  const deleteAlbum = useDeleteAlbum();
  const [title, setTitle] = useState(album.title);
  const [description, setDescription] = useState(album.description ?? "");
  const [eventDate, setEventDate] = useState(album.event_date?.slice(0, 10) ?? "");
  const [backgroundEnabled, setBackgroundEnabled] = useState(album.background_enabled);
  const [interval, setInterval] = useState(album.background_interval_seconds);
  const [transition, setTransition] = useState<BackgroundTransition>(album.background_transition);

  useEffect(() => {
    setTitle(album.title);
    setDescription(album.description ?? "");
    setEventDate(album.event_date?.slice(0, 10) ?? "");
    setBackgroundEnabled(album.background_enabled);
    setInterval(album.background_interval_seconds);
    setTransition(album.background_transition);
  }, [album]);

  async function save(event: FormEvent) {
    event.preventDefault();
    await updateAlbum.mutateAsync({
      id: album.id,
      body: {
        title,
        description: description || null,
        event_date: eventDate ? new Date(eventDate).toISOString() : null,
        background_enabled: backgroundEnabled,
        background_interval_seconds: interval,
        background_transition: transition,
      },
    });
  }

  async function remove() {
    if (!window.confirm(t("gallery.deleteAlbumConfirm"))) return;
    await deleteAlbum.mutateAsync(album.id);
  }

  const selectedPhotos = album.photos.filter((photo) => photo.use_as_background).length;

  return (
    <form onSubmit={save} className="mb-8 border border-border bg-card/70 p-5">
      <div className="mb-4 flex items-center gap-2 text-copper">
        <Settings2 size={18} aria-hidden="true" />
        <h3 className="font-display text-2xl font-bold uppercase">{t("gallery.manage")}</h3>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="grid gap-2 text-sm font-semibold">
          {t("gallery.albumTitle")}
          <input
            required
            minLength={2}
            maxLength={180}
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            className="border border-border bg-background px-4 py-3 font-normal"
          />
        </label>
        <label className="grid gap-2 text-sm font-semibold">
          {t("gallery.eventDate")}
          <input
            type="date"
            value={eventDate}
            onChange={(event) => setEventDate(event.target.value)}
            className="border border-border bg-background px-4 py-3 font-normal"
          />
        </label>
        <label className="grid gap-2 text-sm font-semibold md:col-span-2">
          {t("gallery.description")}
          <textarea
            maxLength={2000}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            className="min-h-24 border border-border bg-background px-4 py-3 font-normal"
          />
        </label>
      </div>

      <div className="mt-5 border-t border-border pt-5">
        <label className="flex items-start gap-3">
          <input
            type="checkbox"
            checked={backgroundEnabled}
            onChange={(event) => setBackgroundEnabled(event.target.checked)}
            className="mt-1 size-4 accent-primary"
          />
          <span>
            <span className="block font-semibold">{t("gallery.backgroundSource")}</span>
            <span className="mt-1 block text-sm text-muted-foreground">
              {t("gallery.backgroundSourceHelp")}
            </span>
          </span>
        </label>

        {backgroundEnabled ? (
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <label className="grid gap-2 text-sm font-semibold">
              {t("gallery.backgroundInterval")}
              <input
                type="number"
                min={3}
                max={30}
                value={interval}
                onChange={(event) => setInterval(Number(event.target.value))}
                className="border border-border bg-background px-4 py-3 font-normal"
              />
            </label>
            <label className="grid gap-2 text-sm font-semibold">
              {t("gallery.backgroundTransition")}
              <select
                value={transition}
                onChange={(event) => setTransition(event.target.value as BackgroundTransition)}
                className="border border-border bg-background px-4 py-3 font-normal"
              >
                <option value="fade">{t("gallery.transition.fade")}</option>
                <option value="slide">{t("gallery.transition.slide")}</option>
                <option value="zoom">{t("gallery.transition.zoom")}</option>
              </select>
            </label>
            {selectedPhotos === 0 ? (
              <p className="text-sm text-copper md:col-span-2">
                {t("gallery.backgroundEmptyWarning")}
              </p>
            ) : null}
          </div>
        ) : null}
      </div>

      <div className="mt-5 flex flex-wrap gap-3">
        <button
          disabled={updateAlbum.isPending || deleteAlbum.isPending}
          className="bg-primary px-5 py-3 font-bold disabled:opacity-60"
        >
          {updateAlbum.isPending ? t("gallery.saving") : t("gallery.save")}
        </button>
        <button
          type="button"
          disabled={updateAlbum.isPending || deleteAlbum.isPending}
          onClick={() => void remove()}
          className="inline-flex items-center gap-2 border border-copper px-5 py-3 font-bold text-copper disabled:opacity-60"
        >
          <Trash2 size={17} aria-hidden="true" />
          {t("gallery.deleteAlbum")}
        </button>
      </div>
      {updateAlbum.isError || deleteAlbum.isError ? (
        <p role="alert" className="mt-4 text-sm text-copper">
          {t("gallery.manageError")}
        </p>
      ) : null}
    </form>
  );
}
