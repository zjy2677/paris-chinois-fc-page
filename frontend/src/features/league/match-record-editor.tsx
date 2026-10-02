import { useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { MatchEvent } from "@/types/football";
import { useI18n } from "@/i18n/i18n-provider";
import { usePlayers, useSaveMatchRecord, type MatchDetail } from "./league-api";

type EditableEvent = MatchEvent & { key: string };

export function MatchRecordEditor({ match }: { match: MatchDetail }) {
  const { t } = useI18n();
  const players = usePlayers();
  const save = useSaveMatchRecord(match.id);
  const [editing, setEditing] = useState(false);
  const [description, setDescription] = useState(match.description ?? "");
  const [homeScore, setHomeScore] = useState(match.score?.[0]?.toString() ?? "");
  const [awayScore, setAwayScore] = useState(match.score?.[1]?.toString() ?? "");
  const [events, setEvents] = useState<EditableEvent[]>([]);

  useEffect(() => {
    setDescription(match.description ?? "");
    setHomeScore(match.score?.[0]?.toString() ?? "");
    setAwayScore(match.score?.[1]?.toString() ?? "");
    setEvents(match.events.map((event) => ({ ...event, key: event.id ?? crypto.randomUUID() })));
  }, [match]);

  const addEvent = (event_type: MatchEvent["event_type"]) => {
    const player = players.data?.[0];
    if (!player) return;
    setEvents((current) => [
      ...current,
      {
        key: crypto.randomUUID(),
        event_type,
        player_id: player.id,
        assist_player_id: null,
        minute: null,
      },
    ]);
  };
  const update = (key: string, values: Partial<EditableEvent>) =>
    setEvents((current) =>
      current.map((event) => (event.key === key ? { ...event, ...values } : event)),
    );

  const submit = () => {
    const score = (value: string) => (value === "" ? null : Number(value));
    save.mutate(
      {
        description: description.trim() || null,
        home_score: score(homeScore),
        away_score: score(awayScore),
        events: events.map(({ event_type, player_id, assist_player_id, minute }) => ({
          event_type,
          player_id,
          assist_player_id,
          minute,
        })),
      },
      { onSuccess: () => setEditing(false) },
    );
  };

  if (!editing) {
    return (
      <Button className="mt-8" onClick={() => setEditing(true)}>
        {t("match.editRecord")}
      </Button>
    );
  }

  return (
    <section
      className="mt-8 border border-border bg-card p-5 md:p-8"
      aria-label={t("match.editRecord")}
    >
      <h2 className="font-display text-3xl font-bold uppercase">{t("match.editRecord")}</h2>
      {match.sourceType === "manual" ? (
        <div className="mt-6 flex items-end gap-3">
          <label className="text-sm">
            {t("Home")}
            <Input
              className="mt-2 w-24"
              min="0"
              type="number"
              value={homeScore}
              onChange={(e) => setHomeScore(e.target.value)}
            />
          </label>
          <span className="pb-2">—</span>
          <label className="text-sm">
            {t("Away")}
            <Input
              className="mt-2 w-24"
              min="0"
              type="number"
              value={awayScore}
              onChange={(e) => setAwayScore(e.target.value)}
            />
          </label>
        </div>
      ) : (
        <p className="mt-4 text-sm text-muted-foreground">{t("match.syncedScoreHint")}</p>
      )}

      <div className="mt-8 space-y-3">
        {events.map((event) => (
          <div
            key={event.key}
            className="grid gap-3 border-t border-border pt-4 md:grid-cols-[140px_1fr_1fr_100px_auto]"
          >
            <select
              className="h-9 border border-input bg-background px-3 text-sm"
              value={event.event_type}
              onChange={(e) =>
                update(event.key, {
                  event_type: e.target.value as MatchEvent["event_type"],
                  assist_player_id: e.target.value === "goal" ? event.assist_player_id : null,
                })
              }
            >
              <option value="goal">{t("match.goal")}</option>
              <option value="yellow_card">{t("match.yellowCard")}</option>
              <option value="red_card">{t("match.redCard")}</option>
            </select>
            <select
              className="h-9 border border-input bg-background px-3 text-sm"
              value={event.player_id}
              onChange={(e) => update(event.key, { player_id: e.target.value })}
            >
              {players.data?.map((player) => (
                <option key={player.id} value={player.id}>
                  {player.name}
                </option>
              ))}
            </select>
            {event.event_type === "goal" ? (
              <select
                className="h-9 border border-input bg-background px-3 text-sm"
                value={event.assist_player_id ?? ""}
                onChange={(e) => update(event.key, { assist_player_id: e.target.value || null })}
              >
                <option value="">{t("match.noAssist")}</option>
                {players.data
                  ?.filter((p) => p.id !== event.player_id)
                  .map((player) => (
                    <option key={player.id} value={player.id}>
                      {player.name}
                    </option>
                  ))}
              </select>
            ) : (
              <span />
            )}
            <Input
              aria-label={t("match.minute")}
              min="0"
              max="130"
              placeholder={t("match.minute")}
              type="number"
              value={event.minute ?? ""}
              onChange={(e) =>
                update(event.key, { minute: e.target.value === "" ? null : Number(e.target.value) })
              }
            />
            <Button
              aria-label={t("match.removeEvent")}
              size="icon"
              variant="ghost"
              onClick={() =>
                setEvents((current) => current.filter((item) => item.key !== event.key))
              }
            >
              <Trash2 />
            </Button>
          </div>
        ))}
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button
          type="button"
          variant="outline"
          onClick={() => addEvent("goal")}
          disabled={!players.data?.length}
        >
          <Plus />
          {t("match.addGoal")}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => addEvent("yellow_card")}
          disabled={!players.data?.length}
        >
          <Plus />
          {t("match.addCard")}
        </Button>
      </div>
      <label className="mt-8 block text-sm font-medium">
        {t("match.description")}
        <Textarea
          className="mt-2 min-h-40"
          maxLength={10000}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </label>
      {save.isError && (
        <p className="mt-4 text-sm text-destructive" role="alert">
          {t("match.saveError")}
        </p>
      )}
      <div className="mt-6 flex gap-3">
        <Button onClick={submit} disabled={save.isPending}>
          {save.isPending ? t("auth.pending") : t("blog.saveChanges")}
        </Button>
        <Button variant="ghost" onClick={() => setEditing(false)}>
          {t("blog.cancelEdit")}
        </Button>
      </div>
    </section>
  );
}
