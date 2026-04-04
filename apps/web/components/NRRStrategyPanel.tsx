"use client";

import { useEffect, useState } from "react";
import type { NRRStrategyResponse, NRRScenario } from "@/lib/types";
import { getNRRStrategy } from "@/lib/api";
import type { TeamKey } from "@/lib/teams";

const FEASIBILITY_STYLES: Record<string, string> = {
  comfortable: "bg-success/20 text-success",
  achievable: "bg-warning/20 text-warning",
  difficult: "bg-orange-400/20 text-orange-400",
  unlikely: "bg-danger/20 text-danger",
};

function formatNRR(nrr: number) {
  return nrr >= 0 ? `+${nrr.toFixed(3)}` : nrr.toFixed(3);
}

export default function NRRStrategyPanel({ teamKey }: { teamKey: TeamKey }) {
  const [strategy, setStrategy] = useState<NRRStrategyResponse | null>(null);

  useEffect(() => {
    getNRRStrategy(teamKey.toLowerCase())
      .then(setStrategy)
      .catch(() => {});
  }, [teamKey]);

  if (!strategy || strategy.scenarios.length === 0) return null;

  return (
    <section className="mb-10">
      <h2 className="text-lg font-semibold uppercase tracking-wider text-text-muted mb-4">
        NRR Strategy
      </h2>
      <div className="bg-surface rounded-xl p-5 md:p-6">
        <p className="text-sm text-text-muted mb-4">
          vs {strategy.next_match.opponent} at{" "}
          {strategy.next_match.venue.replace(/_/g, " ")} (avg 1st innings:{" "}
          {strategy.next_match.venue_avg_1st})
        </p>

        <div className="space-y-4">
          {strategy.scenarios.map((s, i) => (
            <ScenarioCard key={i} scenario={s} />
          ))}
        </div>
      </div>
    </section>
  );
}

function ScenarioCard({ scenario }: { scenario: NRRScenario }) {
  if (scenario.target === "loss_scenario") {
    return (
      <div className="bg-surface-2 rounded-lg p-4 border border-danger/30">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-danger">If you lose</span>
        </div>
        <p className="text-xs text-text-muted">{scenario.description}</p>
        <p className="text-xs text-text-muted mt-1">
          NRR drops to{" "}
          <span className="font-mono text-danger">
            {formatNRR(scenario.worst_case_nrr || 0)}
          </span>{" "}
          (rank #{scenario.resulting_rank})
        </p>
      </div>
    );
  }

  const label =
    scenario.target === "overtake_above"
      ? `To overtake ${scenario.target_team} (${formatNRR(scenario.target_nrr || 0)})`
      : `To stay above ${scenario.target_team} (${formatNRR(scenario.target_nrr || 0)})`;

  const feasStyle =
    FEASIBILITY_STYLES[scenario.feasibility || ""] || "bg-surface-2 text-text-muted";

  return (
    <div className="bg-surface-2 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">{label}</span>
        {scenario.feasibility && (
          <span
            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${feasStyle}`}
          >
            {scenario.feasibility}
          </span>
        )}
      </div>
      {scenario.bat_first && (
        <p className="text-xs text-text-muted">
          {scenario.bat_first.description}
        </p>
      )}
      {scenario.chase && (
        <p className="text-xs text-text-muted">
          {scenario.chase.description}
        </p>
      )}
    </div>
  );
}
