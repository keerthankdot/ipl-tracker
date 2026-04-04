"use client";

import { TEAMS, type TeamKey } from "@/lib/teams";
import type { ImpactResponse } from "@/lib/types";

function formatDelta(delta: number) {
  if (delta > 0) return `+${delta.toFixed(1)}%`;
  if (delta < 0) return `${delta.toFixed(1)}%`;
  return "0.0%";
}

interface ImpactPanelProps {
  impact: ImpactResponse;
  teamKey: TeamKey;
}

export default function ImpactPanel({ impact, teamKey }: ImpactPanelProps) {
  const m = impact.match;
  const t1Data = TEAMS[m.team1 as TeamKey];
  const t2Data = TEAMS[m.team2 as TeamKey];
  const myImpact = impact.impact.find((i) => i.team === teamKey);
  const otherAffected = impact.impact
    .filter((i) => i.most_affected && i.team !== teamKey)
    .slice(0, 3);

  const ifT1Me = impact.if_team1_wins.find((r) => r.team === teamKey);
  const ifT2Me = impact.if_team2_wins.find((r) => r.team === teamKey);

  return (
    <section className="mb-10">
      <h2 className="text-lg font-semibold uppercase tracking-wider text-text-muted mb-6">
        Next Match Impact
      </h2>
      <div className="bg-surface rounded-xl p-5 md:p-6">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm text-text-muted">
            {new Date(m.date + "T00:00:00").toLocaleDateString("en-IN", {
              month: "short",
              day: "numeric",
            })}
          </span>
        </div>

        <div className="flex items-center gap-3 mb-4">
          <span className="font-bold" style={{ color: t1Data?.color }}>
            {m.team1}
          </span>
          <div className="flex-1 h-2 bg-surface-2 rounded-full overflow-hidden flex">
            <div
              className="h-full rounded-l-full"
              style={{
                width: `${m.team1_win_pct}%`,
                backgroundColor: t1Data?.color,
              }}
            />
            <div
              className="h-full rounded-r-full"
              style={{
                width: `${m.team2_win_pct}%`,
                backgroundColor: t2Data?.color,
              }}
            />
          </div>
          <span className="font-bold" style={{ color: t2Data?.color }}>
            {m.team2}
          </span>
        </div>

        <div className="text-sm text-text-muted mb-4 text-center font-mono">
          {m.team1_win_pct}% / {m.team2_win_pct}%
        </div>

        {myImpact && ifT1Me && ifT2Me && (
          <div className="space-y-2 mb-4">
            <div className="flex justify-between items-center">
              <span className="text-sm">If {m.team1} wins</span>
              <span className="font-mono text-sm">
                Top 4: {ifT1Me.top4_pct}%{" "}
                <span
                  className={
                    myImpact.if_team1_wins >= 0 ? "text-success" : "text-danger"
                  }
                >
                  ({formatDelta(myImpact.if_team1_wins)})
                </span>
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">If {m.team2} wins</span>
              <span className="font-mono text-sm">
                Top 4: {ifT2Me.top4_pct}%{" "}
                <span
                  className={
                    myImpact.if_team2_wins >= 0 ? "text-success" : "text-danger"
                  }
                >
                  ({formatDelta(myImpact.if_team2_wins)})
                </span>
              </span>
            </div>
          </div>
        )}

        {otherAffected.length > 0 && (
          <div className="border-t border-border pt-3">
            <p className="text-xs text-text-muted mb-2">Most affected teams</p>
            <div className="flex flex-wrap gap-3 text-xs font-mono">
              {otherAffected.map((t) => (
                <span key={t.team} className="text-text-muted">
                  {t.team}:{" "}
                  <span
                    className={
                      t.if_team1_wins >= 0 ? "text-success" : "text-danger"
                    }
                  >
                    {formatDelta(t.if_team1_wins)}
                  </span>{" "}
                  /{" "}
                  <span
                    className={
                      t.if_team2_wins >= 0 ? "text-success" : "text-danger"
                    }
                  >
                    {formatDelta(t.if_team2_wins)}
                  </span>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
