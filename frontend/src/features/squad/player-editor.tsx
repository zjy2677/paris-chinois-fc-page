import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/i18n/i18n-provider";
import type { Player } from "@/types/football";
import { PlayerApiError, savePlayer, SQUAD_SEASON } from "./squad-api";

import { positions } from "./squad-api";

const inputClass =
  "mt-2 w-full border border-border bg-background px-3 py-3 text-base focus:outline-none focus:ring-2 focus:ring-primary";
/** Edit or create a season player, refreshing squad queries and closing after a successful save. */
export function PlayerEditor({ player, onClose }: { player?: Player; onClose: () => void }) {
  const { t, c } = useI18n();
  const cache = useQueryClient();
  const [name, setName] = useState(player?.display_name ?? "");
  const [description, setDescription] = useState(player?.description ?? "");
  const [photo, setPhoto] = useState(player?.photo_url ?? "");
  const [number, setNumber] = useState(player?.shirt_number?.toString() ?? "");
  const [position, setPosition] = useState<Player["position"]>(player?.position ?? "Midfielders");
  const save = useMutation({
    mutationFn: () =>
      savePlayer(
        {
          display_name: name.trim(),
          description: description.trim() || null,
          photo_url: photo.trim() || null,
          shirt_number: number ? Number(number) : null,
          position,
        },
        player?.id,
      ),
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
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <label className="block text-sm">
                {t("squad.position")}
                <select
                  aria-label={t("squad.position")}
                  value={position}
                  onChange={(e) => setPosition(e.target.value as Player["position"])}
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
            <label className="block text-sm">
              {t("squad.photo")}
              <input
                type="url"
                pattern="https://.*"
                maxLength={2048}
                value={photo}
                onChange={(e) => setPhoto(e.target.value)}
                placeholder="https://…"
                aria-describedby="photo-help"
                className={inputClass}
              />
            </label>
            <p id="photo-help" className="text-sm text-muted-foreground">
              {t("squad.photoHelp")}
            </p>
          </fieldset>
          {save.isError && (
            <p role="alert" className="text-sm text-copper">
              {t(
                save.error instanceof PlayerApiError && save.error.status === 409
                  ? "squad.numberConflict"
                  : "squad.saveError",
              )}
            </p>
          )}
          <div className="flex justify-end gap-3">
            <Button type="button" variant="outline" disabled={save.isPending} onClick={onClose}>
              {t("squad.cancel")}
            </Button>
            <Button type="submit" disabled={save.isPending || !name.trim()}>
              {t(save.isPending ? "squad.saving" : "squad.save")}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
