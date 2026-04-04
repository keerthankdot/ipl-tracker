"use client";

import { useEffect, useState } from "react";
import { useParams, redirect } from "next/navigation";
import Link from "next/link";
import { getTeamBySlug, TEAMS, type TeamKey } from "@/lib/teams";
import { getMatchDetail } from "@/lib/api";
import type { MatchDetailResponse } from "@/lib/types";

const BADGE_STYLES: Record<string, string> = {
  MUST_WIN: "bg-danger/20 text-danger border border-danger",
  FAVORED: "bg-success/20 text-success border border-success",
  TOSS_UP: "bg-warning/20 text-warning border border-warning",
  TOUGH: "bg-orange-400/20 text-orange-400 border border-orange-400",
  UPSET_NEEDED: "bg-danger/30 text-danger border border-danger",
};

const BADGE_LABELS: Record<string, string> = {
  MUST_WIN: "MUST WIN",
  FAVORED: "FAVORED",
  TOSS_UP: "TOSS-UP",
  TOUGH: "TOUGH",
  UPSET_NEEDED: "UPSET NEEDED",
};

function StatRow({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="flex justify-between items-baseline py-1.5 border-b border-border/30">
      <span className="text-sm text-text-muted">{label}</span>
      <div className="text-right">
        <span className="font-mono text-sm">{value}</span>
        {sub && <span className="text-xs text-text-muted ml-1">{sub}</span>}
      </div>
    </div>
  );
}

export default function MatchDeepDive() {
  const params = useParams<{ team: string; matchId: string }>();
  const teamKey = getTeamBySlug(params.team);
  const [data, setData] = useState<MatchDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!teamKey) return;
    getMatchDetail(params.matchId, teamKey)
      .then(setData)
      .catch((err) => setError(err.message));
  }, [teamKey, params.matchId]);

  if (!teamKey) {
    redirect("/");
  }

  const team = TEAMS[teamKey];
  const oppData = data ? TEAMS[data.opponent as TeamKey] : null;

  return (
    <main className="min-h-screen px-6 py-8 md:px-12 md:py-12 max-w-4xl mx-auto">
      <Link
        href={`/${params.team}`}
        className="text-text-muted hover:text-text transition-colors text-sm mb-8 inline-block"
      >
        &larr; Back to {team.name}
      </Link>

      {error && (
        <div className="bg-surface rounded-xl p-8 text-center">
          <p className="text-text-muted">{error}</p>
        </div>
      )}

      {!data && !error && (
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-40 bg-surface rounded-xl animate-pulse" />
          ))}
        </div>
      )}

      {data && (
        <>
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl md:text-3xl font-bold">
                <span style={{ color: team.color }}>{data.team}</span>
                {" vs "}
                <span style={{ color: oppData?.color }}>{data.opponent}</span>
              </h1>
              {data.classification && (
                <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${BADGE_STYLES[data.classification] || ""}`}>
                  {BADGE_LABELS[data.classification] || data.classification}
                </span>
              )}
            </div>
            <p className="text-text-muted text-sm">
              {new Date(data.date + "T00:00:00").toLocaleDateString("en-IN", {
                weekday: "long",
                month: "long",
                day: "numeric",
                year: "numeric",
              })}
              {" \u00B7 "}
              {data.time} IST
              {" \u00B7 "}
              {data.venue.name}
              {data.is_home ? " (Home)" : ""}
            </p>
            <div className="h-1 w-24 rounded mt-2" style={{ backgroundColor: team.color }} />
          </div>

          {/* Completed result */}
          {data.result && (
            <section className="mb-8 bg-surface rounded-xl p-5">
              <h2 className="text-lg font-semibold uppercase tracking-wider text-text-muted mb-3">
                Result
              </h2>
              <div className={`text-xl font-bold mb-2 ${data.result.result === "won" ? "text-success" : "text-danger"}`}>
                {data.result.result === "won" ? "\u2713 Won" : "\u2717 Lost"}
              </div>
              <p className="font-mono text-sm">
                {data.team}: {data.result.score_team1} ({data.result.overs_team1})
              </p>
              <p className="font-mono text-sm">
                {data.opponent}: {data.result.score_team2} ({data.result.overs_team2})
              </p>
            </section>
          )}

          {/* Win Probability + Impact */}
          {data.win_prob != null && (
            <section className="mb-8 bg-surface rounded-xl p-5">
              <h2 className="text-lg font-semibold uppercase tracking-wider text-text-muted mb-4">
                Win Probability
              </h2>
              <div className="flex items-center gap-3 mb-3">
                <span className="font-bold text-sm" style={{ color: team.color }}>{data.team}</span>
                <div className="flex-1 h-3 bg-surface-2 rounded-full overflow-hidden flex">
                  <div
                    className="h-full rounded-l-full"
                    style={{ width: `${data.win_prob * 100}%`, backgroundColor: team.color }}
                  />
                  <div
                    className="h-full rounded-r-full"
                    style={{ width: `${(1 - data.win_prob) * 100}%`, backgroundColor: oppData?.color }}
                  />
                </div>
                <span className="font-bold text-sm" style={{ color: oppData?.color }}>{data.opponent}</span>
              </div>
              <div className="text-center font-mono text-sm text-text-muted">
                {Math.round(data.win_prob * 100)}% / {Math.round((1 - data.win_prob) * 100)}%
              </div>
              {data.impact && (
                <div className="mt-3 text-sm text-text-muted">
                  Impact: {data.impact.impact_pct.toFixed(1)}% swing on your Top 4 odds (currently {data.impact.team_top4_pct}%)
                </div>
              )}
            </section>
          )}

          {/* Venue Intelligence */}
          <section className="mb-8 bg-surface rounded-xl p-5">
            <h2 className="text-lg font-semibold uppercase tracking-wider text-text-muted mb-4">
              Venue Intelligence
            </h2>
            <p className="text-sm text-text-muted mb-4 italic">{data.venue.notes}</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8">
              <div>
                <StatRow label="Avg 1st innings" value={data.venue.avg_1st_innings} />
                <StatRow label="Avg 2nd innings" value={data.venue.avg_2nd_innings} />
                <StatRow label="Bat first win %" value={`${data.venue.bat_first_win_pct}%`} />
                <StatRow label="Chase win %" value={`${data.venue.chase_win_pct}%`} />
              </div>
              <div>
                <StatRow label="Pace wickets" value={`${data.venue.pace_wicket_pct}%`} />
                <StatRow label="Spin wickets" value={`${data.venue.spin_wicket_pct}%`} />
                {data.venue.altitude_m && (
                  <StatRow label="Altitude" value={`${data.venue.altitude_m}m`} />
                )}
                {data.venue.boundary_avg_m && (
                  <StatRow label="Boundary avg" value={`${data.venue.boundary_avg_m}m`} />
                )}
                <StatRow label="Dew factor" value={data.venue.dew_factor} />
              </div>
            </div>
          </section>

          {/* Weather Forecast */}
          {data.weather && (
            <section className="mb-8 bg-surface rounded-xl p-5">
              <h2 className="text-lg font-semibold uppercase tracking-wider text-text-muted mb-4">
                Weather Forecast
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <div className="bg-surface-2 rounded-lg p-3 text-center">
                  <div className="font-mono text-lg font-bold">{data.weather.temperature_c}&deg;C</div>
                  <div className="text-xs text-text-muted">Temperature</div>
                </div>
                <div className="bg-surface-2 rounded-lg p-3 text-center">
                  <div className="font-mono text-lg font-bold">{data.weather.humidity_pct}%</div>
                  <div className="text-xs text-text-muted">Humidity</div>
                </div>
                <div className="bg-surface-2 rounded-lg p-3 text-center">
                  <div className="font-mono text-lg font-bold">{data.weather.wind_speed_kmh} km/h</div>
                  <div className="text-xs text-text-muted">Wind</div>
                </div>
                <div className="bg-surface-2 rounded-lg p-3 text-center">
                  <div className="font-mono text-lg font-bold">{data.weather.rain_probability_pct}%</div>
                  <div className="text-xs text-text-muted">Rain chance</div>
                </div>
              </div>
              <p className="text-sm text-text-muted capitalize mb-4">{data.weather.description}</p>
              <div className={`rounded-lg p-4 ${
                data.weather.dew.level === "heavy" ? "bg-info/20 border border-info" :
                data.weather.dew.level === "moderate" ? "bg-warning/20 border border-warning" :
                "bg-surface-2 border border-border"
              }`}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-bold uppercase">
                    {data.weather.dew.level === "none" ? "No Dew" : `${data.weather.dew.level} Dew`}
                  </span>
                </div>
                <p className="text-xs text-text-muted">{data.weather.dew.impact}</p>
              </div>
              <p className="text-xs text-text-muted mt-3">Source: OpenWeatherMap</p>
            </section>
          )}

          {/* Toss Analysis */}
          <section className="mb-8 bg-surface rounded-xl p-5">
            <h2 className="text-lg font-semibold uppercase tracking-wider text-text-muted mb-4">
              Toss Analysis
            </h2>
            <div className="flex items-center gap-4 mb-3">
              <div className="flex-1 bg-surface-2 rounded-lg p-3 text-center">
                <div className="font-mono text-lg font-bold">{data.toss.bat_first_win_pct}%</div>
                <div className="text-xs text-text-muted">Bat first wins</div>
              </div>
              <div className="flex-1 bg-surface-2 rounded-lg p-3 text-center">
                <div className="font-mono text-lg font-bold">{data.toss.chase_win_pct}%</div>
                <div className="text-xs text-text-muted">Chase wins</div>
              </div>
            </div>
            <p className="text-sm">
              Recommended: <span className="font-medium">{data.toss.recommendation}</span>
            </p>
            {data.toss.dew_factor !== "light" && (
              <p className="text-xs text-text-muted mt-1">
                Dew factor: {data.toss.dew_factor} (may affect bowling grip in 2nd innings)
              </p>
            )}
          </section>

          {/* Head-to-Head */}
          <section className="mb-8 bg-surface rounded-xl p-5">
            <h2 className="text-lg font-semibold uppercase tracking-wider text-text-muted mb-4">
              Head-to-Head
            </h2>
            <div className="flex items-center gap-4 mb-3">
              <div className="flex-1 bg-surface-2 rounded-lg p-3 text-center">
                <div className="font-mono text-2xl font-bold" style={{ color: team.color }}>
                  {data.h2h.my_wins}
                </div>
                <div className="text-xs text-text-muted">{data.team} wins</div>
              </div>
              <div className="text-text-muted text-sm">vs</div>
              <div className="flex-1 bg-surface-2 rounded-lg p-3 text-center">
                <div className="font-mono text-2xl font-bold" style={{ color: oppData?.color }}>
                  {data.h2h.opponent_wins}
                </div>
                <div className="text-xs text-text-muted">{data.opponent} wins</div>
              </div>
            </div>
            <p className="text-sm text-text-muted text-center">
              {data.h2h.total} matches played
              {" \u00B7 "}
              {data.h2h.my_win_pct}% win rate for {data.team}
            </p>
          </section>

          {/* Key Players */}
          {data.players && (data.players.team1_players.length > 0 || data.players.team2_players.length > 0) && (
            <section className="mb-8 bg-surface rounded-xl p-5">
              <h2 className="text-lg font-semibold uppercase tracking-wider text-text-muted mb-4">
                Key Players
              </h2>
              {[
                { label: data.team, players: data.players.team1_players, color: team.color },
                { label: data.opponent, players: data.players.team2_players, color: oppData?.color },
              ].map((group) => (
                group.players.length > 0 && (
                  <div key={group.label} className="mb-4 last:mb-0">
                    <h3 className="text-sm font-bold mb-2" style={{ color: group.color }}>
                      {group.label}
                    </h3>
                    <div className="space-y-2">
                      {group.players.map((p) => (
                        <div key={p.id} className="bg-surface-2 rounded-lg p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium">{p.name}</span>
                            <span className="text-xs text-text-muted capitalize">{p.role}</span>
                          </div>
                          <div className="flex flex-wrap gap-x-4 text-xs font-mono text-text-muted">
                            {p.summary.batting && (
                              <>
                                <span>{p.summary.batting.innings} inn</span>
                                <span>{p.summary.batting.total_runs} runs</span>
                                <span>SR {p.summary.batting.strike_rate}</span>
                              </>
                            )}
                            {p.summary.bowling && (
                              <>
                                <span>{p.summary.bowling.wickets} wkts</span>
                                <span>Econ {p.summary.bowling.economy}</span>
                              </>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              ))}
              <p className="text-xs text-text-muted mt-3">Stats from IPL 2026 season</p>
            </section>
          )}
        </>
      )}
    </main>
  );
}
