"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { TEAMS, TEAM_KEYS, type TeamKey } from "@/lib/teams";

export default function Home() {
  const router = useRouter();

  function handlePick(team: TeamKey) {
    localStorage.setItem("winpath_team", team);
    router.push(`/${team.toLowerCase()}`);
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 py-12">
      <motion.div
        className="text-center mb-12"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-3">
          WIN PATH
        </h1>
        <p className="text-text-muted text-lg">
          Your Team&apos;s Roadmap to the IPL Trophy
        </p>
      </motion.div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 max-w-5xl w-full">
        {TEAM_KEYS.map((key, i) => {
          const team = TEAMS[key];
          const isGT = key === "GT";
          return (
            <motion.button
              key={key}
              onClick={() => handlePick(key)}
              className="relative bg-surface rounded-xl p-5 text-left cursor-pointer border border-transparent transition-colors"
              style={{ borderLeftWidth: 4, borderLeftColor: team.color }}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                delay: i * 0.05,
                type: "spring",
                stiffness: 200,
                damping: 20,
              }}
              whileHover={{
                scale: 1.02,
                borderColor: isGT ? "#555" : team.color,
              }}
            >
              {isGT && (
                <div className="absolute inset-0 rounded-xl border border-border pointer-events-none" />
              )}
              <span className="block text-xl font-bold">{key}</span>
              <span className="block text-sm text-text-muted mt-1 leading-tight">
                {team.name}
              </span>
              <span className="block text-sm text-text-muted">{team.city}</span>
            </motion.button>
          );
        })}
      </div>

      <p className="text-text-muted text-sm mt-12">by Ascnd Technologies</p>
    </main>
  );
}
