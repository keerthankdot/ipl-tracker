"use client";

import { useState, useEffect } from "react";
import { TEAMS, type TeamKey } from "@/lib/teams";
import { getSchedule } from "@/lib/api";
import type { Match } from "@/lib/types";

interface TeamScheduleProps {
  teamKey: TeamKey;
}

export default function TeamSchedule({ teamKey }: TeamScheduleProps) {
  const [completed, setCompleted] = useState<Match[]>([]);
  const [upcoming, setUpcoming] = useState<Match[]>([]);
  const [showAll, setShowAll] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getSchedule(teamKey, "completed"),
      getSchedule(teamKey, "upcoming"),
    ])
      .then(([comp, up]) => {
        setCompleted(comp.matches);
        setUpcoming(up.matches);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [teamKey]);

  const team = TEAMS[teamKey];
  const visibleUpcoming = showAll ? upcoming : upcoming.slice(0, 5);

  if (loading) {
    return (
      <section className="mb-10">
        <h2 className="text-lg font-semibold uppercase tracking-wider text-text-muted mb-6">
          Schedule
        </h2>
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="bg-surface rounded-lg p-4 animate-pulse h-16"
            />
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="mb-10">
      <h2 className="text-lg font-semibold uppercase tracking-wider text-text-muted mb-6">
        Schedule
      </h2>

      {completed.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-text-muted mb-3">
            Completed
          </h3>
          <div className="space-y-2">
            {completed.map((m) => {
              const won = m.winner === teamKey;
              const opponent =
                m.team1 === teamKey ? m.team2 : m.team1;
              const oppData = TEAMS[opponent as TeamKey];
              return (
                <div
                  key={m.id}
                  className="bg-surface rounded-lg px-4 py-3 flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`text-xs font-bold w-6 text-center ${
                        won ? "text-success" : "text-danger"
                      }`}
                    >
                      {won ? "W" : "L"}
                    </span>
                    <span className="text-sm">
                      vs{" "}
                      <span
                        className="font-medium"
                        style={{ color: oppData?.color }}
                      >
                        {opponent}
                      </span>
                    </span>
                  </div>
                  <div className="text-right">
                    {m.score_team1 && m.score_team2 && (
                      <span className="text-xs font-mono text-text-muted">
                        {m.score_team1} vs {m.score_team2}
                      </span>
                    )}
                    <span className="text-xs text-text-muted ml-3">
                      {new Date(m.date + "T00:00:00").toLocaleDateString(
                        "en-IN",
                        { month: "short", day: "numeric" }
                      )}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {upcoming.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-text-muted mb-3">
            Upcoming
          </h3>
          <div className="space-y-2">
            {visibleUpcoming.map((m) => {
              const opponent =
                m.team1 === teamKey ? m.team2 : m.team1;
              const oppData = TEAMS[opponent as TeamKey];
              return (
                <div
                  key={m.id}
                  className="bg-surface rounded-lg px-4 py-3 flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-text-muted w-6 text-center font-mono">
                      #{m.match_number}
                    </span>
                    <span className="text-sm">
                      vs{" "}
                      <span
                        className="font-medium"
                        style={{ color: oppData?.color }}
                      >
                        {opponent}
                      </span>
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-text-muted">
                    <span>{m.venue}</span>
                    <span className="font-mono">{m.time} IST</span>
                    <span>
                      {new Date(m.date + "T00:00:00").toLocaleDateString(
                        "en-IN",
                        { month: "short", day: "numeric" }
                      )}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
          {upcoming.length > 5 && (
            <button
              onClick={() => setShowAll(!showAll)}
              className="mt-3 text-sm text-text-muted hover:text-text transition-colors cursor-pointer"
            >
              {showAll
                ? "Show less"
                : `Show all ${upcoming.length} upcoming matches`}
            </button>
          )}
        </div>
      )}
    </section>
  );
}
