import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { useAccount } from "@/features/auth/auth-api";
import { useI18n } from "@/i18n/i18n-provider";
import { playerRequest } from "./squad-api";

type Attribute = { id: string; label: string; kind: "strength" | "weakness"; level: number };
type Draft = Omit<Attribute, "id"> & { id?: string };
const levels = [1, 2, 3, 4, 5] as const;
const colors = [
  "border-slate-400/60 bg-slate-400/15 text-slate-200",
  "border-blue-400/60 bg-blue-400/15 text-blue-300",
  "border-yellow-400/60 bg-yellow-400/15 text-yellow-200",
  "border-orange-400/60 bg-orange-400/15 text-orange-300",
  "border-red-400/60 bg-red-500/15 text-red-300",
];
const fieldClass = "w-full rounded border border-border bg-background p-3 text-base";

export function PlayerAttributes({ playerId }: { playerId: string }) {
  const { t } = useI18n();
  const account = useAccount();
  const admin = account.data?.role === "admin";
  const cache = useQueryClient();
  const path = `/players/${encodeURIComponent(playerId)}/attributes`;
  const queryKey = ["players", "attributes", playerId];
  const query = useQuery({
    queryKey,
    enabled: typeof window !== "undefined",
    queryFn: ({ signal }) => playerRequest<Attribute[]>(path, "GET", undefined, signal),
  });
  const [draft, setDraft] = useState<Draft | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const mutation = useMutation({
    mutationFn: async (action: { draft: Draft } | { deleteId: string }): Promise<void> => {
      if ("deleteId" in action) {
        await playerRequest<void>(`${path}/${action.deleteId}`, "DELETE");
        return;
      }
      const { id, ...body } = action.draft;
      await playerRequest<Attribute>(id ? `${path}/${id}` : path, id ? "PUT" : "POST", body);
    },
    onSuccess: async () => {
      setDraft(null);
      setDeleting(null);
      await cache.invalidateQueries({ queryKey });
    },
  });
  return (
    <section className="mt-10" aria-labelledby="player-attributes">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="player-attributes" className="text-xl font-semibold">
          {t("attributes.title")}
        </h2>
        {admin && !draft && (
          <Button
            variant="outline"
            disabled={mutation.isPending}
            onClick={() => {
              mutation.reset();
              setDeleting(null);
              setDraft({ label: "", kind: "strength", level: 3 });
            }}
          >
            {t("attributes.add")}
          </Button>
        )}
      </div>
      <p className="mt-2 text-sm text-muted-foreground">{t("attributes.hint")}</p>
      <div className="mt-3 flex flex-wrap gap-2" aria-label={t("attributes.levels")}>
        {levels.map((level) => (
          <span key={level} className={`rounded border px-2 py-1 text-xs ${colors[level - 1]}`}>
            {t("attributes.level", { level })}
          </span>
        ))}
      </div>
      {query.isPending ? (
        <p role="status" className="mt-4">
          {t("squad.loading")}
        </p>
      ) : query.isError ? (
        <div role="alert" className="mt-4">
          <p>{t("squad.loadError")}</p>
          <Button variant="outline" onClick={() => query.refetch()}>
            {t("squad.retry")}
          </Button>
        </div>
      ) : (
        <div className="mt-5 grid gap-5 sm:grid-cols-2">
          {(["strength", "weakness"] as const).map((kind) => (
            <div key={kind}>
              <h3 className="mb-3 text-sm font-semibold">{t(`attributes.${kind}`)}</h3>
              <ul className="flex flex-wrap gap-2">
                {query.data
                  ?.filter((tag) => tag.kind === kind)
                  .map((tag) => (
                    <li
                      key={tag.id}
                      className={`max-w-full rounded-lg border p-3 ${colors[tag.level - 1]}`}
                    >
                      <span className="break-words font-medium">{tag.label}</span>
                      <span className="ml-2 whitespace-nowrap text-xs">
                        {t("attributes.level", { level: tag.level })}
                      </span>
                      {admin && (
                        <div className="mt-2 flex flex-wrap gap-3 text-xs">
                          <button
                            type="button"
                            className="underline underline-offset-4"
                            disabled={mutation.isPending}
                            onClick={() => {
                              mutation.reset();
                              setDeleting(null);
                              setDraft({ ...tag });
                            }}
                          >
                            {t("squad.edit")}
                          </button>
                          <button
                            type="button"
                            className="underline underline-offset-4"
                            disabled={mutation.isPending}
                            onClick={() => {
                              mutation.reset();
                              setDraft(null);
                              setDeleting(tag.id);
                            }}
                          >
                            {t("attributes.remove")}
                          </button>
                          {deleting === tag.id && (
                            <>
                              <button
                                type="button"
                                className="font-bold underline underline-offset-4"
                                disabled={mutation.isPending}
                                onClick={() => mutation.mutate({ deleteId: tag.id })}
                              >
                                {t("attributes.confirmRemove")}
                              </button>
                              <button
                                type="button"
                                disabled={mutation.isPending}
                                onClick={() => setDeleting(null)}
                              >
                                {t("squad.cancel")}
                              </button>
                            </>
                          )}
                        </div>
                      )}
                    </li>
                  ))}
              </ul>
              {!query.data?.some((tag) => tag.kind === kind) && (
                <p className="text-sm text-muted-foreground">{t("attributes.empty")}</p>
              )}
            </div>
          ))}
        </div>
      )}
      {admin && draft && (
        <form
          className="mt-5 space-y-4 rounded-lg border border-border p-4"
          onSubmit={(event) => {
            event.preventDefault();
            mutation.mutate({ draft: { ...draft, label: draft.label.trim() } });
          }}
        >
          <fieldset disabled={mutation.isPending} className="space-y-4">
            <label className="block space-y-2 text-sm">
              <span>{t("attributes.label")}</span>
              <input
                autoFocus
                required
                maxLength={80}
                className={fieldClass}
                value={draft.label}
                onChange={(event) => setDraft({ ...draft, label: event.target.value })}
              />
            </label>
            <label className="block space-y-2 text-sm">
              <span>{t("attributes.kind")}</span>
              <select
                className={fieldClass}
                value={draft.kind}
                onChange={(event) =>
                  setDraft({ ...draft, kind: event.target.value as Attribute["kind"] })
                }
              >
                <option value="strength">{t("attributes.strength")}</option>
                <option value="weakness">{t("attributes.weakness")}</option>
              </select>
            </label>
            <fieldset>
              <legend className="mb-2 text-sm">{t("attributes.levels")}</legend>
              <div className="flex flex-wrap gap-2">
                {levels.map((level) => (
                  <label
                    key={level}
                    className={`flex cursor-pointer items-center gap-2 rounded border p-3 ${colors[level - 1]}`}
                  >
                    <input
                      type="radio"
                      name="attribute-level"
                      value={level}
                      checked={draft.level === level}
                      onChange={() => setDraft({ ...draft, level })}
                    />
                    {level}
                  </label>
                ))}
              </div>
            </fieldset>
            <div className="flex gap-3">
              <Button type="submit" disabled={!draft.label.trim()}>
                {t(mutation.isPending ? "squad.saving" : "attributes.save")}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setDraft(null);
                  mutation.reset();
                }}
              >
                {t("squad.cancel")}
              </Button>
            </div>
          </fieldset>
        </form>
      )}
      {admin && mutation.isError && (
        <p role="alert" className="mt-3 text-red-300">
          {t("squad.saveError")}
        </p>
      )}
    </section>
  );
}
