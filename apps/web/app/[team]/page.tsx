"use client";

import { useEffect, useState } from "react";
import { useParams, redirect } from "next/navigation";
import Link from "next/link";
import { getTeamBySlug, TEAMS } from "@/lib/teams";
import {
  getStandings,
  simulate,
  getSchedule,
  getImpact,
  getWinPath,
} from "@/lib/api";
import type {
  StandingsResponse,
  SimulateResponse,
  ImpactResponse,
  Match,
  WinPathResponse,
} from "@/lib/types";

import ProbabilityBars from "@/components/ProbabilityBars";
import NRRDisplay from "@/components/NRRDisplay";
import ImpactPanel from "@/components/ImpactPanel";
import WinPathRoadmap from "@/components/WinPathRoadmap";
import { SkeletonCard } from "@/components/SkeletonLoaders";
import ScenarioTheater from "@/components/ScenarioTheater";
import TeamSchedule from "@/components/TeamSchedule";
import NRRStrategyPanel from "@/components/NRRStrategyPanel";
import StandingsTable from "@/components/StandingsTable";

export default function TeamDashboard() {
  const params = useParams<{ team: string }>();
  const teamKey = getTeamBySlug(params.team);

  const [standings, setStandings] = useState<StandingsResponse | null>(null);
  const [simulation, setSimulation] = useState<SimulateResponse | null>(null);
  const [impact, setImpact] = useState<ImpactResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [winPath, setWinPath] = useState<WinPathResponse | null>(null);
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

    if (teamKey) {
      getWinPath(teamKey.toLowerCase()).then(setWinPath).catch(() => {});
    }

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

      {/* Team Header */}
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
          <ProbabilityBars
            teamResult={teamResult}
            team={team}
            simulation={simulation}
            loading={loading}
          />

          <NRRDisplay standings={standings} teamKey={teamKey} />

          <NRRStrategyPanel teamKey={teamKey} />

          {impact && <ImpactPanel impact={impact} teamKey={teamKey} />}

          {winPath ? (
            <WinPathRoadmap winPath={winPath} team={team} />
          ) : (
            !loading && null
          )}
          {!winPath && loading && (
            <section className="mb-10">
              <h2 className="text-lg font-semibold uppercase tracking-wider text-text-muted mb-4">
                Win Path
              </h2>
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <SkeletonCard key={i} />
                ))}
              </div>
            </section>
          )}

          <ScenarioTheater
            upcomingMatches={upcomingMatches}
            teamKey={teamKey}
            simulation={simulation}
          />

          <TeamSchedule teamKey={teamKey} />

          <StandingsTable
            standings={standings}
            teamKey={teamKey}
            team={team}
            loading={loading}
          />
        </>
      )}
    </main>
  );
}
