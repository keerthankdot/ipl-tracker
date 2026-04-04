"use client";

import { TEAMS, type TeamKey } from "@/lib/teams";
import type { StandingsResponse } from "@/lib/types";

function formatNRR(nrr: number) {
  return nrr >= 0 ? `+${nrr.toFixed(3)}` : nrr.toFixed(3);
}

interface NRRDisplayProps {
  standings: StandingsResponse | null;
  teamKey: TeamKey;
}

export default function NRRDisplay({ standings, teamKey }: NRRDisplayProps) {
  if (!standings) return null;

  const sorted = [...standings.standings].sort((a, b) => b.nrr - a.nrr);
  const myIndex = sorted.findIndex((s) => s.team === teamKey);
  const myStanding = sorted[myIndex];

  if (!myStanding) return null;

  const nrrRank = myIndex + 1;
  const teamAbove = myIndex > 0 ? sorted[myIndex - 1] : null;
  const teamBelow = myIndex < sorted.length - 1 ? sorted[myIndex + 1] : null;
  const team = TEAMS[teamKey];

  const minNRR = sorted[sorted.length - 1].nrr;
  const maxNRR = sorted[0].nrr;
  const nrrRange = maxNRR - minNRR || 1;

  function nrrToPercent(nrr: number) {
    return ((nrr - minNRR) / nrrRange) * 100;
  }

  return (
    <section className="mb-10">
      <h2 className="text-lg font-semibold uppercase tracking-wider text-text-muted mb-6">
        Net Run Rate
      </h2>
      <div className="bg-surface rounded-xl p-5 md:p-6">
        <div className="flex items-baseline gap-3 mb-1">
          <span
            className={`font-mono text-2xl font-bold ${
              myStanding.nrr >= 0 ? "text-success" : "text-danger"
            }`}
          >
            {formatNRR(myStanding.nrr)}
          </span>
          <span className="text-text-muted text-sm">
            Rank #{nrrRank} of 10
          </span>
        </div>

        <div className="relative h-8 bg-surface-2 rounded-full my-5">
          {sorted.map((s) => {
            const isMe = s.team === teamKey;
            const left = nrrToPercent(s.nrr);
            const teamData = TEAMS[s.team as TeamKey];
            return (
              <div
                key={s.team}
                className="absolute top-1/2 -translate-y-1/2 rounded-full"
                style={{
                  left: `${Math.max(2, Math.min(98, left))}%`,
                  width: isMe ? 14 : 8,
                  height: isMe ? 14 : 8,
                  backgroundColor: isMe
                    ? team.color
                    : teamData?.color || "#555",
                  opacity: isMe ? 1 : 0.5,
                  transform: `translate(-50%, -50%)`,
                  zIndex: isMe ? 10 : 1,
                  border: isMe ? "2px solid white" : "none",
                }}
                title={`${s.team}: ${formatNRR(s.nrr)}`}
              />
            );
          })}
        </div>

        <div className="flex justify-between text-xs text-text-muted font-mono">
          <span>{formatNRR(minNRR)}</span>
          <span>{formatNRR(maxNRR)}</span>
        </div>

        <div className="mt-4 space-y-1 text-sm">
          {teamAbove && (
            <p className="text-text-muted">
              Behind:{" "}
              <span
                className="font-medium"
                style={{ color: TEAMS[teamAbove.team as TeamKey]?.color }}
              >
                {teamAbove.team}
              </span>{" "}
              <span className="font-mono">({formatNRR(teamAbove.nrr)})</span>
            </p>
          )}
          {teamBelow && (
            <p className="text-text-muted">
              Ahead of:{" "}
              <span
                className="font-medium"
                style={{ color: TEAMS[teamBelow.team as TeamKey]?.color }}
              >
                {teamBelow.team}
              </span>{" "}
              <span className="font-mono">({formatNRR(teamBelow.nrr)})</span>
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
