import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/i18n/i18n-provider";
import type { Player } from "@/types/football";
import {
  PlayerApiError,
  PlayerPhotoUploadError,
  savePlayer,
  SQUAD_SEASON,
  uploadPlayerPhoto,
} from "./squad-api";

import { positions } from "./squad-api";

const inputClass =
  "mt-2 w-full border border-border bg-background px-3 py-3 text-base focus:outline-none focus:ring-2 focus:ring-primary";
/** Edit or create a season player, refreshing squad queries and closing after a successful save. */
export function PlayerEditor({ player, onClose }: { player?: Player; onClose: () => void }) {
  const { t, c } = useI18n();
  const cache = useQueryClient();
  const [name, setName] = useState(player?.display_name ?? "");
  const [chineseName, setChineseName] = useState(player?.chinese_name ?? "");
  const [description, setDescription] = useState(player?.description ?? "");
  const [photo, setPhoto] = useState(player?.photo_url ?? "");
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoMode, setPhotoMode] = useState<"none" | "upload" | "url">(
    player?.has_uploaded_photo ? "upload" : player?.photo_url ? "url" : "none",
  );
  const [number, setNumber] = useState(player?.shirt_number?.toString() ?? "");
  const [position, setPosition] = useState<Player["position"]>(player?.position ?? "Midfielders");
  const [alternatePositions, setAlternatePositions] = useState<Player["alternate_positions"]>(
    player?.alternate_positions ?? [],
  );
  const [persistedId, setPersistedId] = useState<string | undefined>(player?.id);
  const save = useMutation({
    mutationFn: async () => {
      const saved = await savePlayer(
        {
          display_name: name.trim(),
          chinese_name: chineseName.trim(),
          description: description.trim() || null,
          ...(photoMode === "url"
            ? { photo_url: photo.trim() }
            : photoMode === "none"
              ? { photo_url: null }
              : {}),
          shirt_number: number ? Number(number) : null,
          position,
          alternate_positions: alternatePositions,
        },
        persistedId,
      );
      setPersistedId(saved.id);
      if (photoMode === "upload" && photoFile) await uploadPlayerPhoto(saved.id, photoFile);
      return saved;
    },
    onSuccess: async () => {
      await cache.invalidateQueries({ queryKey: ["players"] });
      onClose();
    },
  });
  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open && !save.isPending) onClose();
      }}
    >
      <DialogContent className="max-h-[90dvh] w-[calc(100%-2rem)] overflow-y-auto sm:max-w-lg">
        <DialogTitle>{t(player ? "squad.edit" : "squad.add")}</DialogTitle>
        <DialogDescription>{t("squad.formIntro", { season: SQUAD_SEASON })}</DialogDescription>
        <form
          className="space-y-4"
          onSubmit={(event) => {
            event.preventDefault();
            save.mutate();
          }}
        >
          <fieldset disabled={save.isPending} className="space-y-4 disabled:opacity-60">
            <label className="block text-sm">
              {t("profile.description")}
              <textarea
                aria-label={t("profile.description")}
                maxLength={2000}
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className={inputClass}
              />
            </label>
            <label className="block text-sm">
              {t("squad.name")}
              <input
                required
                maxLength={150}
                value={name}
                onChange={(e) => setName(e.target.value)}
                className={inputClass}
              />
            </label>
            <label className="block text-sm">
              {t("squad.chineseName")}
              <input
                required
                maxLength={150}
                value={chineseName}
                onChange={(e) => setChineseName(e.target.value)}
                className={inputClass}
              />
            </label>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <label className="block text-sm">
                {t("squad.position")}
                <select
                  aria-label={t("squad.position")}
                  value={position}
                  required
                  onChange={(e) => {
                    const next = e.target.value as Player["position"];
                    setPosition(next);
                    setAlternatePositions((current) => current.filter((item) => item !== next));
                  }}
                  className={inputClass}
                >
                  {positions.map((p) => (
                    <option key={p} value={p}>
                      {c(p)}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-sm">
                {t("squad.number")}
                <input
                  type="number"
                  min={1}
                  max={2147483647}
                  step={1}
                  value={number}
                  onChange={(e) => setNumber(e.target.value)}
                  className={inputClass}
                />
              </label>
            </div>
            <fieldset className="space-y-3">
              <legend className="text-sm">{t("squad.alternatePositions")}</legend>
              <div className="flex flex-wrap gap-3">
                {positions
                  .filter((item) => item !== position)
                  .map((item) => (
                    <label key={item} className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={alternatePositions.includes(item)}
                        onChange={(event) =>
                          setAlternatePositions((current) =>
                            event.target.checked
                              ? [...current, item]
                              : current.filter((value) => value !== item),
                          )
                        }
                      />
                      {c(item)}
                    </label>
                  ))}
              </div>
            </fieldset>
            <fieldset className="space-y-3">
              <legend className="text-sm">{t("squad.photo")}</legend>
              <div className="flex flex-wrap gap-4">
                {(["none", "upload", "url"] as const).map((mode) => (
                  <label key={mode} className="flex items-center gap-2 text-sm">
                    <input
                      type="radio"
                      name="photo-mode"
                      checked={photoMode === mode}
                      onChange={() => setPhotoMode(mode)}
                    />
                    {t(`squad.photoMode.${mode}`)}
                  </label>
                ))}
              </div>
              {photoMode === "url" && (
                <input
                  required
                  type="url"
                  pattern="https://.*"
                  maxLength={2048}
                  value={photo}
                  onChange={(e) => setPhoto(e.target.value)}
                  placeholder="https://…"
                  aria-describedby="photo-help"
                  className={inputClass}
                />
              )}
              {photoMode === "upload" && (
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  required={!player?.has_uploaded_photo}
                  onChange={(event) => setPhotoFile(event.target.files?.[0] ?? null)}
                  aria-describedby="photo-help"
                  className={inputClass}
                />
              )}
            </fieldset>
            <p id="photo-help" className="text-sm text-muted-foreground">
              {t("squad.photoHelp")}
            </p>
          </fieldset>
          {save.isError && (
            <p role="alert" className="text-sm text-copper">
              {t(
                save.error instanceof PlayerApiError && save.error.status === 409
                  ? "squad.numberConflict"
                  : save.error instanceof PlayerPhotoUploadError
                    ? "squad.photoUploadError"
                    : "squad.saveError",
              )}
            </p>
          )}
          <div className="flex justify-end gap-3">
            <Button type="button" variant="outline" disabled={save.isPending} onClick={onClose}>
              {t("squad.cancel")}
            </Button>
            <Button
              type="submit"
              disabled={
                save.isPending ||
                !name.trim() ||
                !chineseName.trim() ||
                (photoMode === "url" && !photo.trim()) ||
                (photoMode === "upload" && !photoFile && !player?.has_uploaded_photo)
              }
            >
              {t(save.isPending ? "squad.saving" : "squad.save")}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
