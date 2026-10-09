import { Link } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRef, useState, type PointerEvent } from "react";
import { useAccount } from "@/features/auth/auth-api";
import { useI18n } from "@/i18n/i18n-provider";
import { localizedPlayerName } from "@/lib/player-name";
import type { Match } from "@/types/football";
import { BoardPlayerIcon } from "./board-player";
import {
  FormationError,
  formationRequest,
  useFormation,
  type BoardPlayer,
  type Placement,
} from "./formation-api";
import { placePlayer } from "./formation-utils";
import { KickoffCountdown } from "./kickoff-countdown";

const actionClass =
  "rounded border border-border px-3 py-2 text-sm hover:border-copper focus-visible:outline focus-visible:outline-copper disabled:opacity-50";

export function TacticalBoard({ match }: { match: Match }) {
  const account = useAccount();
  // The uncached endpoint decides visibility, even while public match data is stale.
  if (account.isPending) return null;
  const viewer = account.data?.id ?? "public";
  return (
    <Board key={`${match.id}:${viewer}:${account.data?.role}`} matchId={match.id} viewer={viewer} />
  );
}

function Board({ matchId, viewer }: { matchId: string; viewer: string }) {
  const { t, language, c } = useI18n();
  const query = useFormation(matchId, viewer);
  const client = useQueryClient();
  const [draft, setDraft] = useState<Placement[] | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const pitch = useRef<HTMLDivElement>(null);
  const bench = useRef<HTMLDivElement>(null);
  const drag = useRef<{
    id: string;
    x: number;
    y: number;
    moved: boolean;
    original: Placement[] | null;
  } | null>(null);
  const skipClick = useRef(false);
  const save = useMutation({
    mutationFn: (items: Placement[]) => formationRequest(matchId, items),
    onSuccess: (data) => {
      client.setQueryData(["formation", matchId, viewer], data);
      setDraft(null);
    },
    onError: () => {
      void query.refetch();
    },
  });
  if (query.isError) {
    if (query.error instanceof FormationError && [401, 403].includes(query.error.status))
      return null;
    return (
      <section className="mt-10">
        <p role="alert">{t("formation.loadError")}</p>
        <button className={actionClass} onClick={() => void query.refetch()}>
          {t("formation.retry")}
        </button>
      </section>
    );
  }
  if (!query.data) return null;
  const board = query.data;
  const editable = board.editable && !save.isPending;
  const items = board.editable ? (draft ?? board.placements) : board.placements;
  const selectedPlayer = board.players.find((player) => player.id === selected);
  const move = (id: string, destination: "pitch" | "bench", x = 50, y = 50) => {
    if (!editable) return;
    save.reset();
    setDraft((current) => placePlayer(current ?? board.placements, id, destination, x, y));
  };
  const coordinates = (x: number, y: number) => {
    const box = pitch.current?.getBoundingClientRect();
    if (!box || x < box.left || x > box.right || y < box.top || y > box.bottom) return null;
    return { x: ((x - box.left) / box.width) * 100, y: ((y - box.top) / box.height) * 100 };
  };
  const pointerDown = (event: PointerEvent<HTMLButtonElement>, id: string) => {
    if (!editable || event.button !== 0) return;
    skipClick.current = false;
    drag.current = { id, x: event.clientX, y: event.clientY, moved: false, original: draft };
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const pointerMove = (event: PointerEvent<HTMLButtonElement>) => {
    if (!drag.current || !editable) return;
    if (Math.hypot(event.clientX - drag.current.x, event.clientY - drag.current.y) > 6)
      drag.current.moved = true;
    if (!drag.current.moved) return;
    const point = coordinates(event.clientX, event.clientY);
    if (
      point &&
      items.some((item) => item.player_id === drag.current?.id && item.placement === "pitch")
    )
      move(drag.current.id, "pitch", point.x, point.y);
  };
  const pointerUp = (event: PointerEvent<HTMLButtonElement>) => {
    const active = drag.current;
    drag.current = null;
    if (!active?.moved) return;
    skipClick.current = true;
    const point = coordinates(event.clientX, event.clientY);
    const box = bench.current?.getBoundingClientRect();
    if (point) move(active.id, "pitch", point.x, point.y);
    else if (
      box &&
      event.clientX >= box.left &&
      event.clientX <= box.right &&
      event.clientY >= box.top &&
      event.clientY <= box.bottom
    )
      move(active.id, "bench");
    else setDraft(active.original);
  };
  const token = (player: BoardPlayer) => (
    <button
      type="button"
      aria-pressed={selected === player.id}
      aria-label={localizedPlayerName(player.display_name, player.chinese_name, language)}
      className={`w-16 rounded p-1 sm:w-20 ${editable ? "touch-none cursor-grab" : "cursor-pointer"} ${selected === player.id ? "ring-2 ring-copper" : "focus-visible:ring-2 focus-visible:ring-copper"}`}
      onPointerDown={(event) => pointerDown(event, player.id)}
      onPointerMove={pointerMove}
      onPointerUp={pointerUp}
      onPointerCancel={() => {
        if (drag.current) setDraft(drag.current.original);
        drag.current = null;
      }}
      onClick={(event) => {
        event.stopPropagation();
        if (skipClick.current) {
          skipClick.current = false;
          return;
        }
        setSelected(player.id);
      }}
      onKeyDown={(event) => {
        const item = items.find((entry) => entry.player_id === player.id);
        const delta = {
          ArrowLeft: [-2, 0],
          ArrowRight: [2, 0],
          ArrowUp: [0, -2],
          ArrowDown: [0, 2],
        }[event.key];
        if (editable && item?.placement === "pitch" && delta) {
          event.preventDefault();
          move(player.id, "pitch", (item.x ?? 50) + delta[0]!, (item.y ?? 50) + delta[1]!);
        }
      }}
    >
      <BoardPlayerIcon player={player} />
    </button>
  );
  return (
    <section
      className="mt-10 rounded-lg border border-border bg-card p-4 sm:p-6"
      aria-labelledby="formation-title"
    >
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <h2 id="formation-title" className="font-display text-3xl font-bold">
          {t(board.status === "final" ? "formation.final" : "formation.title")}
        </h2>
        <KickoffCountdown kickoff={board.kickoff_at} status={board.status} />
      </div>
      {editable && (
        <p className="mb-4 text-sm text-muted-foreground">{t("formation.instructions")}</p>
      )}
      <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(14rem,1fr)]">
        <div>
          <div
            ref={pitch}
            className="relative mx-auto aspect-[3/4] w-full max-w-xl overflow-hidden rounded-lg border border-white/30 bg-emerald-950"
            onClick={(event) => {
              if (selected && editable) {
                const point = coordinates(event.clientX, event.clientY);
                if (point) move(selected, "pitch", point.x, point.y);
              }
            }}
          >
            <svg
              aria-hidden="true"
              viewBox="0 0 300 400"
              className="pointer-events-none absolute inset-0 h-full w-full"
              preserveAspectRatio="none"
            >
              <rect width="300" height="400" fill="#124c37" />
              {[0, 80, 160, 240, 320].map((y) => (
                <rect key={y} y={y} width="300" height="40" fill="#ffffff" opacity=".035" />
              ))}
              <g fill="none" stroke="#fff" strokeOpacity=".5" strokeWidth="1.2">
                <rect x="12" y="12" width="276" height="376" />
                <path d="M12 200H288" />
                <circle cx="150" cy="200" r="35" />
                <path d="M70 12V72H230V12 M112 12V34H188V12 M70 388V328H230V388 M112 388V366H188V388" />
                <path d="M125 72Q150 99 175 72 M125 328Q150 301 175 328" />
              </g>
              <g fill="white" opacity=".65">
                <circle cx="150" cy="200" r="2" />
                <circle cx="150" cy="53" r="2" />
                <circle cx="150" cy="347" r="2" />
              </g>
            </svg>
            {items
              .filter((item) => item.placement === "pitch")
              .map((item) => {
                const player = board.players.find((entry) => entry.id === item.player_id);
                return player ? (
                  <div
                    key={item.player_id}
                    className="absolute"
                    style={{
                      left: `clamp(2rem, ${item.x}%, calc(100% - 2rem))`,
                      top: `clamp(3rem, ${item.y}%, calc(100% - 3rem))`,
                      transform: "translate(-50%, -50%)",
                    }}
                  >
                    {token(player)}
                  </div>
                ) : null;
              })}
          </div>
          <div
            ref={bench}
            className="mt-4 min-h-28 rounded-lg border border-dashed border-copper/50 bg-secondary/40 p-3"
          >
            <h3 className="mb-2 text-sm font-semibold text-copper">{t("formation.bench")}</h3>
            <div className="flex flex-wrap gap-2">
              {items
                .filter((item) => item.placement === "bench")
                .map((item) => {
                  const player = board.players.find((entry) => entry.id === item.player_id);
                  return player ? <div key={player.id}>{token(player)}</div> : null;
                })}
            </div>
          </div>
        </div>
        <div className="space-y-4">
          {selectedPlayer && (
            <div className="rounded border border-border p-4">
              <Link
                to="/team/$playerId"
                params={{ playerId: `player_${selectedPlayer.id}` }}
                className="font-semibold text-copper underline"
              >
                {localizedPlayerName(
                  selectedPlayer.display_name,
                  selectedPlayer.chinese_name,
                  language,
                )}
              </Link>
              {selectedPlayer.position && (
                <p className="mt-1 text-sm">{c(selectedPlayer.position)}</p>
              )}
              {selectedPlayer.description && (
                <p className="mt-2 whitespace-pre-line text-sm text-muted-foreground">
                  {selectedPlayer.description}
                </p>
              )}
              {editable && (
                <div className="mt-3 flex flex-wrap gap-2">
                  <button className={actionClass} onClick={() => move(selectedPlayer.id, "pitch")}>
                    {t("formation.place")}
                  </button>
                  <button className={actionClass} onClick={() => move(selectedPlayer.id, "bench")}>
                    {t("formation.toBench")}
                  </button>
                  <button
                    className={actionClass}
                    onClick={() => {
                      setDraft(items.filter((item) => item.player_id !== selectedPlayer.id));
                      save.reset();
                    }}
                  >
                    {t("formation.remove")}
                  </button>
                </div>
              )}
            </div>
          )}
          {board.editable && (
            <div>
              <h3 className="mb-3 font-semibold">{t("formation.available")}</h3>
              <div className="flex max-h-96 flex-wrap gap-2 overflow-y-auto">
                {board.players
                  .filter((player) => !items.some((item) => item.player_id === player.id))
                  .map((player) => (
                    <div key={player.id}>{token(player)}</div>
                  ))}
              </div>
            </div>
          )}
          {!items.length && <p className="text-sm text-muted-foreground">{t("formation.empty")}</p>}
          {board.editable && (
            <div className="space-y-3">
              <button
                disabled={!draft || save.isPending}
                className="rounded bg-primary px-5 py-3 font-semibold text-primary-foreground disabled:opacity-50"
                onClick={() => save.mutate(items)}
              >
                {t(save.isPending ? "formation.saving" : "formation.save")}
              </button>
              {draft && <p className="text-sm text-copper">{t("formation.unsaved")}</p>}
              {save.isSuccess && (
                <p role="status" className="text-sm">
                  {t("formation.saved")}
                </p>
              )}
              {save.isError && (
                <p role="alert" className="text-sm text-copper">
                  {t("formation.saveError")}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
