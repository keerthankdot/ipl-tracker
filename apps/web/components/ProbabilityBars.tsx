"use client";

import { motion } from "framer-motion";
import { SkeletonBar } from "./SkeletonLoaders";
import type { SimulationTeamResult, SimulateResponse } from "@/lib/types";

interface TeamData {
  name: string;
  short: string;
  color: string;
  city: string;
  home: string;
}

interface ProbabilityBarsProps {
  teamResult: SimulationTeamResult | undefined;
  team: TeamData;
  simulation: SimulateResponse | null;
  loading: boolean;
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

export default function ProbabilityBars({
  teamResult,
  team,
  simulation,
  loading,
}: ProbabilityBarsProps) {
  return (
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
            Based on {simulation.simulations_run.toLocaleString()} simulations
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
  );
}
