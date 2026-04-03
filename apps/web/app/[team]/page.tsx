"use client";

import { useEffect, useState } from "react";
import { useParams, redirect } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { getTeamBySlug, TEAMS, type TeamKey } from "@/lib/teams";
import { getStandings, simulate, getSchedule, getImpact, runScenario } from "@/lib/api";
import type {
  StandingsResponse,
  SimulateResponse,
  ImpactResponse,
  ScenarioOutcome,
  ScenarioResponse,
  Match,
} from "@/lib/types";

function formatNRR(nrr: number) {
  return nrr >= 0 ? `+${nrr.toFixed(3)}` : nrr.toFixed(3);
}

function formatDelta(delta: number) {
  if (delta > 0) return `+${delta.toFixed(1)}%`;
  if (delta < 0) return `${delta.toFixed(1)}%`;
  return "0.0%";
}

function ProbabilityBar({
  label,
  pct,
  color,
  delay,
}: {
  label: string;
  pct: number;
  color: string;
  delay: number;
}) {
  return (
    <div className="flex items-center gap-4">
      <span className="w-12 text-sm font-medium shrink-0">{label}</span>
      <div className="flex-1 h-8 bg-surface-2 rounded-lg overflow-hidden">
        <motion.div
          className="h-full rounded-lg"
          style={{ backgroundColor: color }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{
            type: "spring",
            stiffness: 50,
            damping: 15,
            delay,
          }}
        />
      </div>
      <span className="w-16 text-right font-mono text-lg shrink-0">
        {pct}%
      </span>
    </div>
  );
}

function SkeletonBar() {
  return (
    <div className="flex items-center gap-4">
      <div className="w-12 h-4 bg-surface-2 rounded animate-pulse" />
      <div className="flex-1 h-8 bg-surface-2 rounded-lg animate-pulse" />
      <div className="w-16 h-6 bg-surface-2 rounded animate-pulse" />
    </div>
  );
}

function SkeletonRow() {
  return (
    <tr>
      {Array.from({ length: 7 }).map((_, i) => (
        <td key={i} className="py-2 px-2">
          <div className="h-4 bg-surface-2 rounded animate-pulse" />
        </td>
      ))}
    </tr>
  );
}

function ImpactPanel({
  impact,
  teamKey,
}: {
  impact: ImpactResponse;
  teamKey: TeamKey;
}) {
  const m = impact.match;
  const t1Data = TEAMS[m.team1 as TeamKey];
  const t2Data = TEAMS[m.team2 as TeamKey];
  const myImpact = impact.impact.find((i) => i.team === teamKey);
  const otherAffected = impact.impact
    .filter((i) => i.most_affected && i.team !== teamKey)
    .slice(0, 3);

  const baselineMe = impact.baseline.find((r) => r.team === teamKey);
  const ifT1Me = impact.if_team1_wins.find((r) => r.team === teamKey);
  const ifT2Me = impact.if_team2_wins.find((r) => r.team === teamKey);

  return (
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
            <span className="text-sm">
              If {m.team1} wins
            </span>
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
            <span className="text-sm">
              If {m.team2} wins
            </span>
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
  );
}

export default function TeamDashboard() {
  const params = useParams<{ team: string }>();
  const teamKey = getTeamBySlug(params.team);

  const [standings, setStandings] = useState<StandingsResponse | null>(null);
  const [simulation, setSimulation] = useState<SimulateResponse | null>(null);
  const [impact, setImpact] = useState<ImpactResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [scenarioOpen, setScenarioOpen] = useState(false);
  const [scenarioOutcomes, setScenarioOutcomes] = useState<ScenarioOutcome[]>([]);
  const [scenarioResult, setScenarioResult] = useState<ScenarioResponse | null>(null);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [upcomingMatches, setUpcomingMatches] = useState<Match[]>([]);

  useEffect(() => {
    if (!teamKey) return;
    fetchData();
  }, [teamKey]);

  function fetchData() {
    setLoading(true);
    setError(null);
    Promise.all([getStandings(), simulate()])
      .then(([s, sim]) => {
        setStandings(s);
        setSimulation(sim);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });

    // Fetch impact + upcoming matches independently
    getSchedule(undefined, "upcoming")
      .then((sched) => {
        setUpcomingMatches(sched.matches.slice(0, 8));
        const nextMatch = sched.matches[0];
        if (nextMatch) return getImpact(nextMatch.id);
        return null;
      })
      .then((impactData) => {
        if (impactData) setImpact(impactData);
      })
      .catch(() => {});
  }

  // Debounced scenario API call
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

  if (!teamKey) {
    redirect("/");
  }

  const team = TEAMS[teamKey];
  const teamResult = simulation?.results.find((r) => r.team === teamKey);

  return (
    <main className="min-h-screen px-6 py-8 md:px-12 md:py-12 max-w-4xl mx-auto">
      <Link
        href="/"
        className="text-text-muted hover:text-text transition-colors text-sm mb-8 inline-block"
      >
        &larr; All Teams
      </Link>

      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-bold">{team.name}</h1>
        <div
          className="h-1 w-24 rounded mt-2"
          style={{ backgroundColor: team.color }}
        />
      </div>

      {error && (
        <div className="bg-surface rounded-xl p-8 text-center">
          <p className="text-text-muted mb-4">
            Simulation engine offline. Results will appear when the engine is
            running.
          </p>
          <button
            onClick={fetchData}
            className="bg-surface-2 text-text px-6 py-2 rounded-lg hover:bg-border transition-colors cursor-pointer"
          >
            Retry
          </button>
        </div>
      )}

      {!error && (
        <>
          <section className="mb-10">
            <h2 className="text-lg font-semibold uppercase tracking-wider text-text-muted mb-6">
              Qualification Probability
            </h2>
            <div className="space-y-4">
              {loading || !teamResult ? (
                <>
                  <SkeletonBar />
                  <SkeletonBar />
                  <SkeletonBar />
                </>
              ) : (
                <>
                  <ProbabilityBar
                    label="Top 4"
                    pct={teamResult.top4_pct}
                    color={team.color}
                    delay={0.2}
                  />
                  <ProbabilityBar
                    label="Top 2"
                    pct={teamResult.top2_pct}
                    color={team.color}
                    delay={0.35}
                  />
                  <ProbabilityBar
                    label="Title"
                    pct={teamResult.title_pct}
                    color={team.color}
                    delay={0.5}
                  />
                </>
              )}
            </div>
            {simulation && (
              <div className="mt-4 space-y-1 text-sm text-text-muted">
                <p>
                  Based on {simulation.simulations_run.toLocaleString()}{" "}
                  simulations
                </p>
                <p>
                  Last updated:{" "}
                  {new Date(simulation.generated_at).toLocaleString("en-IN", {
                    timeZone: "Asia/Kolkata",
                    dateStyle: "medium",
                    timeStyle: "short",
                  })}{" "}
                  IST
                </p>
              </div>
            )}
          </section>

          {impact && (
            <section className="mb-10">
              <h2 className="text-lg font-semibold uppercase tracking-wider text-text-muted mb-6">
                Next Match Impact
              </h2>
              <ImpactPanel impact={impact} teamKey={teamKey} />
            </section>
          )}

          {upcomingMatches.length > 0 && (
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
                      const sel = scenarioOutcomes.find(
                        (o) => o.match_id === m.id
                      );
                      const t1Data = TEAMS[m.team1 as TeamKey];
                      const t2Data = TEAMS[m.team2 as TeamKey];
                      const t1Sel = sel?.winner === m.team1;
                      const t2Sel = sel?.winner === m.team2;
                      const isGT1 = m.team1 === "GT";
                      const isGT2 = m.team2 === "GT";

                      return (
                        <div
                          key={m.id}
                          className="flex items-center gap-2 py-1.5"
                        >
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
                                    border:
                                      isGT1 ? "1px solid #555" : undefined,
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
                                    border:
                                      isGT2 ? "1px solid #555" : undefined,
                                  }
                                : undefined
                            }
                          >
                            {m.team2}
                          </button>
                          <span className="text-xs text-text-muted ml-auto">
                            {new Date(m.date + "T00:00:00").toLocaleDateString(
                              "en-IN",
                              { month: "short", day: "numeric" }
                            )}
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
                        Based on{" "}
                        {scenarioResult.simulations_run.toLocaleString()}{" "}
                        simulations
                      </p>
                    </div>
                  )}
                </div>
              )}
            </section>
          )}

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
                            <td className="py-2 px-2 font-medium">
                              {s.team}
                            </td>
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
        </>
      )}
    </main>
  );
}
