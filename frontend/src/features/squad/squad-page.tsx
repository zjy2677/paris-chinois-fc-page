import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { assets } from "@/config/assets";
import { useI18n } from "@/i18n/i18n-provider";
import { PageIntro } from "@/components/layout/page-intro";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import type { Player } from "@/types/football";
import { useAccount } from "@/features/auth/auth-api";
import { PlayerCard } from "./player-card";
import { PlayerEditor } from "./player-editor";
import { PositionFilter, type Position } from "./position-filter";
import { positions, playerRequest, SQUAD_SEASON, useSquad } from "./squad-api";

/** Render the filtered season squad and player management controls for administrators. */
export function SquadPage() {
  const { t, c } = useI18n();
  const account = useAccount();
  const admin = account.data?.role === "admin";
  const squad = useSquad(admin ? account.data?.id : undefined);
  const cache = useQueryClient();
  const [position, setPosition] = useState<Position>("All");
  const [showInactive, setShowInactive] = useState(false);
  const [editor, setEditor] = useState<Player | "new" | null>(null);
  const [removing, setRemoving] = useState<Player | null>(null);
  const changeStatus = useMutation({
    mutationFn: ({ player, active }: { player: Player; active: boolean }) =>
      active
        ? playerRequest(
            `/players/${player.id}?season=${encodeURIComponent(SQUAD_SEASON)}`,
            "PATCH",
            { active: true },
          )
        : playerRequest(`/players/${player.id}`, "DELETE"),
    onSuccess: async () => {
      await cache.invalidateQueries({ queryKey: ["players"] });
      setRemoving(null);
    },
  });
  const players = (squad.data ?? []).filter((p) => p.active || (admin && showInactive));
  const visible = players.filter((p) => position === "All" || p.position === position);
  return (
    <>
      <PageIntro
        backgroundImage={assets.squad}
        title={t("The squad")}
        description={t("2026/2027 season squad")}
      />
      <div className="site-container py-16 md:py-24">
        {admin && (
          <div className="mb-8 flex flex-wrap items-center justify-between gap-4 border-l-2 border-copper bg-card p-5">
            <div>
              <p className="font-semibold">{t("squad.manage")}</p>
              <p className="mt-1 text-sm text-muted-foreground">{t("squad.adminHint")}</p>
            </div>
            <Button onClick={() => setEditor("new")}>{t("squad.add")}</Button>
            <label className="flex w-full items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={showInactive}
                onChange={(e) => setShowInactive(e.target.checked)}
              />
              {t("squad.showInactive")}
            </label>
          </div>
        )}
        <PositionFilter value={position} onChange={setPosition} />
        {squad.isPending ? (
          <p role="status" className="py-12 text-muted-foreground">
            {t("squad.loading")}
          </p>
        ) : squad.isError ? (
          <div role="alert" className="py-12">
            <p>{t("squad.loadError")}</p>
            <Button variant="outline" onClick={() => squad.refetch()} className="mt-4">
              {t("squad.retry")}
            </Button>
          </div>
        ) : visible.length === 0 ? (
          <p className="border border-dashed border-border p-10 text-center text-muted-foreground">
            {t("squad.empty")}
          </p>
        ) : (
          positions
            .filter((group) => visible.some((p) => p.position === group))
            .map((group) => (
              <section key={group} className="mt-14">
                <div className="mb-7 flex items-center gap-6">
                  <h2 className="font-display text-4xl font-bold uppercase md:text-5xl">
                    {c(group)}
                  </h2>
                  <div className="h-px flex-1 bg-border" />
                </div>
                <div className="grid grid-cols-2 gap-3 md:grid-cols-3 md:gap-5 xl:grid-cols-4">
                  {visible
                    .filter((p) => p.position === group)
                    .map((player) => (
                      <PlayerCard
                        key={player.id}
                        player={player}
                        actions={
                          admin ? (
                            <>
                              <Button size="sm" variant="outline" onClick={() => setEditor(player)}>
                                {t("squad.edit")}
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                disabled={changeStatus.isPending}
                                onClick={() => {
                                  changeStatus.reset();
                                  if (player.active) setRemoving(player);
                                  else changeStatus.mutate({ player, active: true });
                                }}
                              >
                                {t(player.active ? "squad.deactivate" : "squad.restore")}
                              </Button>
                            </>
                          ) : undefined
                        }
                      />
                    ))}
                </div>
              </section>
            ))
        )}
        {admin && changeStatus.isError && !removing && (
          <p role="alert" className="mt-4 text-copper">
            {t("squad.saveError")}
          </p>
        )}
      </div>
      {admin && editor && (
        <PlayerEditor
          key={editor === "new" ? "new" : editor.id}
          {...(editor === "new" ? {} : { player: editor })}
          onClose={() => setEditor(null)}
        />
      )}
      <Dialog
        open={admin && removing !== null}
        onOpenChange={(open) => {
          if (!open && !changeStatus.isPending) setRemoving(null);
        }}
      >
        <DialogContent className="w-[calc(100%-2rem)] sm:max-w-lg">
          <DialogTitle>
            {t("squad.deactivateTitle", { name: removing?.display_name ?? "" })}
          </DialogTitle>
          <DialogDescription>{t("squad.deactivateHint")}</DialogDescription>
          {changeStatus.isError && (
            <p role="alert" className="text-copper">
              {t("squad.saveError")}
            </p>
          )}
          <div className="flex flex-wrap justify-end gap-3">
            <Button
              variant="outline"
              disabled={changeStatus.isPending}
              onClick={() => setRemoving(null)}
            >
              {t("squad.cancel")}
            </Button>
            <Button
              disabled={changeStatus.isPending}
              onClick={() => {
                if (removing) changeStatus.mutate({ player: removing, active: false });
              }}
            >
              {t(changeStatus.isPending ? "squad.saving" : "squad.deactivate")}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
