"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { TEAMS, type TeamKey } from "@/lib/teams";
import type { WinPathResponse } from "@/lib/types";

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

interface TeamData {
  name: string;
  short: string;
  color: string;
  city: string;
  home: string;
}

interface WinPathRoadmapProps {
  winPath: WinPathResponse;
  team: TeamData;
}

export default function WinPathRoadmap({ winPath, team }: WinPathRoadmapProps) {
  return (
    <section className="mb-10">
      <h2 className="text-lg font-semibold uppercase tracking-wider text-text-muted mb-4">
        Win Path
      </h2>
      <div className="flex flex-wrap gap-2 text-xs mb-6">
        {winPath.summary.must_wins > 0 && (
          <span className={`px-2 py-0.5 rounded ${BADGE_STYLES.MUST_WIN}`}>
            {winPath.summary.must_wins} must-win
          </span>
        )}
        {winPath.summary.favored > 0 && (
          <span className={`px-2 py-0.5 rounded ${BADGE_STYLES.FAVORED}`}>
            {winPath.summary.favored} favored
          </span>
        )}
        {winPath.summary.toss_ups > 0 && (
          <span className={`px-2 py-0.5 rounded ${BADGE_STYLES.TOSS_UP}`}>
            {winPath.summary.toss_ups} toss-up
          </span>
        )}
        {winPath.summary.tough > 0 && (
          <span className={`px-2 py-0.5 rounded ${BADGE_STYLES.TOUGH}`}>
            {winPath.summary.tough} tough
          </span>
        )}
        {winPath.summary.upset_needed > 0 && (
          <span className={`px-2 py-0.5 rounded ${BADGE_STYLES.UPSET_NEEDED}`}>
            {winPath.summary.upset_needed} upset needed
          </span>
        )}
      </div>

      <div className="space-y-3">
        {winPath.matches.map((m) => {
          const oppData = TEAMS[m.opponent as TeamKey];
          const isMustWin = m.classification === "MUST_WIN";
          const teamSlug = winPath.team.toLowerCase();

          if (m.status === "completed") {
            return (
              <Link key={m.id} href={`/${teamSlug}/match/${m.id}`} className="block">
              <div
                className="bg-surface rounded-lg p-4 border border-border/50 opacity-80 hover:opacity-100 transition-opacity cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span
                      className={`text-sm font-bold ${
                        m.result === "won" ? "text-success" : "text-danger"
                      }`}
                    >
                      {m.result === "won" ? "\u2713 WON" : "\u2717 LOST"}
                    </span>
                    <span className="text-sm text-text-muted ml-2">
                      vs {m.opponent}
                    </span>
                  </div>
                  <span className="text-xs text-text-muted">
                    {new Date(m.date + "T00:00:00").toLocaleDateString("en-IN", {
                      month: "short",
                      day: "numeric",
                    })}
                  </span>
                </div>
                <div className="text-xs text-text-muted mt-1">
                  {m.venue_name}
                  {m.is_home ? " (Home)" : ""}
                  {m.score ? ` \u00B7 ${m.score}` : ""}
                </div>
              </div>
              </Link>
            );
          }

          return (
            <Link key={m.id} href={`/${teamSlug}/match/${m.id}`} className="block">
            <motion.div
              className="bg-surface rounded-lg p-4 hover:bg-surface-2/50 transition-colors cursor-pointer"
              style={{
                borderWidth: isMustWin ? 2 : 1,
                borderStyle: "solid",
                borderColor: isMustWin ? "#EF4444" : "rgba(42,42,58,0.5)",
              }}
              animate={
                isMustWin
                  ? {
                      borderColor: ["#EF4444", "#EF444460", "#EF4444"],
                    }
                  : undefined
              }
              transition={
                isMustWin ? { duration: 2, repeat: Infinity } : undefined
              }
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">
                    vs{" "}
                    <span
                      style={{ color: oppData?.color }}
                      className="font-bold"
                    >
                      {m.opponent}
                    </span>
                  </span>
                  {m.classification && (
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        BADGE_STYLES[m.classification] || ""
                      }`}
                    >
                      {BADGE_LABELS[m.classification] || m.classification}
                    </span>
                  )}
                </div>
                <span className="text-xs text-text-muted">
                  {new Date(m.date + "T00:00:00").toLocaleDateString("en-IN", {
                    month: "short",
                    day: "numeric",
                  })}
                </span>
              </div>

              <div className="text-xs text-text-muted mb-3">
                {m.venue_name}
                {m.is_home ? " (Home)" : ""} {"\u00B7"} {m.venue_city}
              </div>

              <div className="flex items-center gap-3">
                <div className="flex-1 h-2 bg-surface-2 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${(m.win_prob || 0) * 100}%`,
                      backgroundColor: team.color,
                    }}
                  />
                </div>
                <span className="font-mono text-sm w-12 text-right">
                  {Math.round((m.win_prob || 0) * 100)}%
                </span>
                {m.impact != null && (
                  <span className="text-xs text-text-muted">
                    {m.impact.toFixed(1)}% impact
                  </span>
                )}
              </div>
            </motion.div>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
