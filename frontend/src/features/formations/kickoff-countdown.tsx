import { useEffect, useState } from "react";
import { useI18n } from "@/i18n/i18n-provider";
import { countdown } from "./formation-utils";

export function KickoffCountdown({ kickoff, status }: { kickoff: string | null; status: string }) {
  const { t } = useI18n();
  const [now, setNow] = useState<number | null>(null);
  useEffect(() => {
    setNow(Date.now());
    if (status !== "scheduled" || !kickoff || Date.now() >= Date.parse(kickoff)) return;
    const timer = window.setInterval(() => {
      const current = Date.now();
      setNow(current);
      if (current >= Date.parse(kickoff)) window.clearInterval(timer);
    }, 1000);
    return () => window.clearInterval(timer);
  }, [kickoff, status]);
  if (status === "final")
    return <p className="text-sm font-semibold text-copper">{t("formation.final")}</p>;
  if (status !== "scheduled")
    return <p className="text-sm text-muted-foreground">{t("formation.awaitingSchedule")}</p>;
  const time = now === null ? null : countdown(kickoff, now);
  return (
    <p className="text-sm tabular-nums text-copper">
      {time ? t("formation.countdown", time) : t("formation.awaitingSchedule")}
    </p>
  );
}
