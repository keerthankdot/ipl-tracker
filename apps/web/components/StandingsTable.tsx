"use client";

import { SkeletonRow } from "./SkeletonLoaders";
import type { StandingsResponse } from "@/lib/types";
import type { TeamKey } from "@/lib/teams";

function formatNRR(nrr: number) {
  return nrr >= 0 ? `+${nrr.toFixed(3)}` : nrr.toFixed(3);
}

interface TeamData {
  name: string;
  short: string;
  color: string;
  city: string;
  home: string;
}

interface StandingsTableProps {
  standings: StandingsResponse | null;
  teamKey: TeamKey;
  team: TeamData;
  loading: boolean;
}

export default function StandingsTable({
  standings,
  teamKey,
  team,
  loading,
}: StandingsTableProps) {
  return (
    <section>
      <h2 className="text-lg font-semibold uppercase tracking-wider text-text-muted mb-6">
        Current Standings
      </h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-text-muted border-b border-border">
              <th className="text-left py-2 px-2 font-medium">#</th>
              <th className="text-left py-2 px-2 font-medium">Team</th>
              <th className="text-center py-2 px-2 font-medium">P</th>
              <th className="text-center py-2 px-2 font-medium">W</th>
              <th className="text-center py-2 px-2 font-medium">L</th>
              <th className="text-center py-2 px-2 font-medium">Pts</th>
              <th className="text-right py-2 px-2 font-medium">NRR</th>
            </tr>
          </thead>
          <tbody>
            {loading || !standings
              ? Array.from({ length: 10 }).map((_, i) => (
                  <SkeletonRow key={i} />
                ))
              : standings.standings.map((s) => {
                  const isSelected = s.team === teamKey;
                  return (
                    <tr
                      key={s.team}
                      className={
                        isSelected
                          ? "bg-surface-2"
                          : "hover:bg-surface transition-colors"
                      }
                      style={
                        isSelected
                          ? {
                              borderLeft: `3px solid ${team.color}`,
                            }
                          : undefined
                      }
                    >
                      <td className="py-2 px-2 font-mono">{s.rank}</td>
                      <td className="py-2 px-2 font-medium">{s.team}</td>
                      <td className="text-center py-2 px-2 font-mono">
                        {s.played}
                      </td>
                      <td className="text-center py-2 px-2 font-mono">
                        {s.won}
                      </td>
                      <td className="text-center py-2 px-2 font-mono">
                        {s.lost}
                      </td>
                      <td className="text-center py-2 px-2 font-mono font-bold">
                        {s.points}
                      </td>
                      <td
                        className={`text-right py-2 px-2 font-mono ${
                          s.nrr >= 0 ? "text-success" : "text-danger"
                        }`}
                      >
                        {formatNRR(s.nrr)}
                      </td>
                    </tr>
                  );
                })}
          </tbody>
        </table>
      </div>
      {standings && (
        <p className="mt-4 text-sm text-text-muted">
          {standings.matches_completed} of 70 matches completed,{" "}
          {standings.matches_remaining} remaining
        </p>
      )}
    </section>
  );
}
