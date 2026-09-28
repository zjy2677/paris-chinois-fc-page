import { useState } from "react";
import { useI18n } from "@/i18n/i18n-provider";
import { useMatches } from "./league-api";
import { DataState } from "./data-state";
import { MatchCard } from "./match-card";
export function MatchList({
  results = false,
  compact = false,
}: {
  results?: boolean;
  compact?: boolean;
}) {
  const { t } = useI18n();
  const [expanded, setExpanded] = useState(false);
  const query = useMatches();
  if (query.isPending || query.isError)
    return (
      <DataState
        loading={query.isPending}
        error={query.isError}
        retry={() => void query.refetch()}
      />
    );
  const matches = query.data
    .filter((m) => (results ? m.status === "final" : m.status !== "final"))
    .sort((a, b) => {
      if (!a.date) return 1;
      if (!b.date) return -1;
      return (Date.parse(a.date) - Date.parse(b.date)) * (results ? -1 : 1);
    });
  const visible = compact
    ? matches
        .filter(
          (m) =>
            results || (m.status === "scheduled" && (!m.date || Date.parse(m.date) >= Date.now())),
        )
        .slice(0, 1)
    : matches.slice(0, expanded ? undefined : 3);
  if (!visible.length)
    return <DataState empty={results ? "league.noResults" : "league.noFixtures"} />;
  return (
    <>
      {visible.map((match) => (
        <MatchCard key={match.id} match={match} compact={compact} />
      ))}
      {!compact && matches.length > 3 && (
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="button"
            aria-expanded={expanded}
            onClick={() => setExpanded((value) => !value)}
            className="border border-copper px-5 py-3 text-sm font-semibold text-copper transition-colors hover:bg-copper/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-copper"
          >
            {t(expanded ? "league.showLess" : "league.showMore")}
          </button>
        </div>
      )}
    </>
  );
}
