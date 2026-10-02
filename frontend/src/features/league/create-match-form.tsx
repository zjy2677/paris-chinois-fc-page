import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useI18n } from "@/i18n/i18n-provider";
import { useCreateMatch } from "./league-api";

export function CreateMatchForm() {
  const { t } = useI18n();
  const create = useCreateMatch();
  const [open, setOpen] = useState(false);
  const [opponent, setOpponent] = useState("");
  const [competition, setCompetition] = useState("");
  const [date, setDate] = useState("");
  const [isHome, setIsHome] = useState(true);
  const [homeScore, setHomeScore] = useState("");
  const [awayScore, setAwayScore] = useState("");
  const [description, setDescription] = useState("");
  if (!open) return <Button onClick={() => setOpen(true)}>{t("match.create")}</Button>;
  const submit = () =>
    create.mutate(
      {
        opponent_name: opponent,
        competition_name: competition || "Friendly",
        season_label: "2026/2027",
        kickoff_at: date ? new Date(date).toISOString() : null,
        is_home: isHome,
        home_score: homeScore === "" ? null : Number(homeScore),
        away_score: awayScore === "" ? null : Number(awayScore),
        description: description.trim() || null,
      },
      { onSuccess: (match) => window.location.assign(`/matches/${match.id}`) },
    );
  return (
    <section className="border border-border bg-card p-5 md:p-8">
      <h2 className="font-display text-3xl font-bold uppercase">{t("match.create")}</h2>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <label className="text-sm">
          {t("match.opponent")}
          <Input
            className="mt-2"
            required
            value={opponent}
            onChange={(e) => setOpponent(e.target.value)}
          />
        </label>
        <label className="text-sm">
          {t("match.competition")}
          <Input
            className="mt-2"
            placeholder="Friendly"
            value={competition}
            onChange={(e) => setCompetition(e.target.value)}
          />
        </label>
        <label className="text-sm">
          {t("match.date")}
          <Input
            className="mt-2"
            type="datetime-local"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </label>
        <label className="text-sm">
          {t("match.location")}
          <select
            className="mt-2 block h-9 w-full border border-input bg-background px-3"
            value={isHome ? "home" : "away"}
            onChange={(e) => setIsHome(e.target.value === "home")}
          >
            <option value="home">{t("Home")}</option>
            <option value="away">{t("Away")}</option>
          </select>
        </label>
        <label className="text-sm">
          {t("Home")}
          <Input
            className="mt-2"
            min="0"
            type="number"
            value={homeScore}
            onChange={(e) => setHomeScore(e.target.value)}
          />
        </label>
        <label className="text-sm">
          {t("Away")}
          <Input
            className="mt-2"
            min="0"
            type="number"
            value={awayScore}
            onChange={(e) => setAwayScore(e.target.value)}
          />
        </label>
      </div>
      <label className="mt-4 block text-sm">
        {t("match.description")}
        <Textarea
          className="mt-2"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </label>
      {create.isError && <p className="mt-4 text-sm text-destructive">{t("match.saveError")}</p>}
      <div className="mt-6 flex gap-3">
        <Button disabled={!opponent.trim() || create.isPending} onClick={submit}>
          {create.isPending ? t("auth.pending") : t("match.create")}
        </Button>
        <Button variant="ghost" onClick={() => setOpen(false)}>
          {t("blog.cancelEdit")}
        </Button>
      </div>
    </section>
  );
}
