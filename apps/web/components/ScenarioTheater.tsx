"use client";

import { useState, useEffect } from "react";
import { TEAMS, type TeamKey } from "@/lib/teams";
import { runScenario } from "@/lib/api";
import type {
  Match,
  ScenarioOutcome,
  ScenarioResponse,
  SimulateResponse,
} from "@/lib/types";

function formatDelta(delta: number) {
  if (delta > 0) return `+${delta.toFixed(1)}%`;
  if (delta < 0) return `${delta.toFixed(1)}%`;
  return "0.0%";
}

interface ScenarioTheaterProps {
  upcomingMatches: Match[];
  teamKey: TeamKey;
  simulation: SimulateResponse | null;
}

export default function ScenarioTheater({
  upcomingMatches,
  teamKey,
  simulation,
}: ScenarioTheaterProps) {
  const [scenarioOpen, setScenarioOpen] = useState(false);
  const [scenarioOutcomes, setScenarioOutcomes] = useState<ScenarioOutcome[]>(
    []
  );
  const [scenarioResult, setScenarioResult] =
    useState<ScenarioResponse | null>(null);
  const [scenarioLoading, setScenarioLoading] = useState(false);

  useEffect(() => {
    if (scenarioOutcomes.length === 0) {
      setScenarioResult(null);
      return;
    }
    const timer = setTimeout(() => {
      setScenarioLoading(true);
      runScenario(scenarioOutcomes)
        .then((res) => {
          setScenarioResult(res);
          setScenarioLoading(false);
        })
        .catch(() => setScenarioLoading(false));
    }, 500);
    return () => clearTimeout(timer);
  }, [scenarioOutcomes]);

  function toggleOutcome(matchId: string, winner: string) {
    setScenarioOutcomes((prev) => {
      const existing = prev.find((o) => o.match_id === matchId);
      if (existing && existing.winner === winner) {
        return prev.filter((o) => o.match_id !== matchId);
      }
      if (existing) {
        return prev.map((o) =>
          o.match_id === matchId ? { ...o, winner } : o
        );
      }
      return [...prev, { match_id: matchId, winner }];
    });
  }

  if (upcomingMatches.length === 0) return null;

  return (
    <section className="mb-10">
      <button
        onClick={() => setScenarioOpen(!scenarioOpen)}
        className="flex items-center gap-2 text-lg font-semibold uppercase tracking-wider text-text-muted mb-4 cursor-pointer hover:text-text transition-colors"
      >
        <span
          className="text-sm transition-transform"
          style={{
            display: "inline-block",
            transform: scenarioOpen ? "rotate(90deg)" : "rotate(0deg)",
          }}
        >
          &#9654;
        </span>
        Scenario Theater
      </button>

      {scenarioOpen && (
        <div className="bg-surface rounded-xl p-5 md:p-6">
          <p className="text-sm text-text-muted mb-4">
            Toggle match outcomes to see how they affect your team
          </p>

          <div className="space-y-1 mb-4">
            {upcomingMatches.map((m) => {
              const sel = scenarioOutcomes.find((o) => o.match_id === m.id);
              const t1Data = TEAMS[m.team1 as TeamKey];
              const t2Data = TEAMS[m.team2 as TeamKey];
              const t1Sel = sel?.winner === m.team1;
              const t2Sel = sel?.winner === m.team2;
              const isGT1 = m.team1 === "GT";
              const isGT2 = m.team2 === "GT";

              return (
                <div key={m.id} className="flex items-center gap-2 py-1.5">
                  <button
                    onClick={() => toggleOutcome(m.id, m.team1)}
                    className={`px-3 py-1 rounded text-sm font-medium transition-all cursor-pointer ${
                      t1Sel
                        ? "text-white"
                        : "text-text-muted border border-border hover:border-text-muted"
                    }`}
                    style={
                      t1Sel
                        ? {
                            backgroundColor: t1Data?.color,
                            border: isGT1 ? "1px solid #555" : undefined,
                          }
                        : undefined
                    }
                  >
                    {m.team1}
                  </button>
                  <span className="text-text-muted text-xs w-6 text-center">
                    {t1Sel || t2Sel ? "vs" : "\u2014"}
                  </span>
                  <button
                    onClick={() => toggleOutcome(m.id, m.team2)}
                    className={`px-3 py-1 rounded text-sm font-medium transition-all cursor-pointer ${
                      t2Sel
                        ? "text-white"
                        : "text-text-muted border border-border hover:border-text-muted"
                    }`}
                    style={
                      t2Sel
                        ? {
                            backgroundColor: t2Data?.color,
                            border: isGT2 ? "1px solid #555" : undefined,
                          }
                        : undefined
                    }
                  >
                    {m.team2}
                  </button>
                  <span className="text-xs text-text-muted ml-auto">
                    {new Date(m.date + "T00:00:00").toLocaleDateString("en-IN", {
                      month: "short",
                      day: "numeric",
                    })}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="flex items-center justify-between mb-4">
            <span className="text-xs text-text-muted">
              {scenarioOutcomes.length > 0
                ? `${scenarioOutcomes.length} match${scenarioOutcomes.length > 1 ? "es" : ""} predicted`
                : "Select match outcomes above"}
            </span>
            {scenarioOutcomes.length > 0 && (
              <button
                onClick={() => setScenarioOutcomes([])}
                className="text-xs text-text-muted hover:text-text transition-colors cursor-pointer"
              >
                Reset All
              </button>
            )}
          </div>

          {scenarioLoading && (
            <div className="text-sm text-text-muted animate-pulse">
              Simulating...
            </div>
          )}

          {scenarioResult && !scenarioLoading && simulation && (
            <div className="bg-surface-2 rounded-lg p-4">
              <div className="space-y-2">
                {(() => {
                  const base = simulation.results.find(
                    (r) => r.team === teamKey
                  );
                  const scen = scenarioResult.results.find(
                    (r) => r.team === teamKey
                  );
                  const delta = scenarioResult.deltas.find(
                    (d) => d.team === teamKey
                  );
                  if (!base || !scen || !delta) return null;
                  return [
                    {
                      label: "Top 4",
                      b: base.top4_pct,
                      n: scen.top4_pct,
                      d: delta.top4_delta,
                    },
                    {
                      label: "Top 2",
                      b: base.top2_pct,
                      n: scen.top2_pct,
                      d: delta.top2_delta,
                    },
                    {
                      label: "Title",
                      b: base.title_pct,
                      n: scen.title_pct,
                      d: delta.title_delta,
                    },
                  ].map((row) => (
                    <div
                      key={row.label}
                      className="flex items-center justify-between"
                    >
                      <span className="text-sm w-12">{row.label}</span>
                      <span className="font-mono text-sm text-text-muted">
                        {row.b}%
                      </span>
                      <span className="text-text-muted">&rarr;</span>
                      <span className="font-mono text-sm font-bold">
                        {row.n}%
                      </span>
                      <span
                        className={`font-mono text-sm w-16 text-right ${
                          row.d > 0
                            ? "text-success"
                            : row.d < 0
                              ? "text-danger"
                              : "text-text-muted"
                        }`}
                      >
                        {formatDelta(row.d)}
                      </span>
                    </div>
                  ));
                })()}
              </div>
              <p className="text-xs text-text-muted mt-3">
                Based on {scenarioResult.simulations_run.toLocaleString()}{" "}
                simulations
              </p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
