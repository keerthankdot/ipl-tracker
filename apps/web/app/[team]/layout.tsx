import type { Metadata } from "next";
import { TEAMS } from "@/lib/teams";

type Props = {
  params: Promise<{ team: string }>;
  children: React.ReactNode;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { team } = await params;
  const teamKey = team.toUpperCase();
  const teamData = TEAMS[teamKey as keyof typeof TEAMS];

  if (!teamData) {
    return { title: "Team Not Found" };
  }

  let description = `${teamData.name}'s path to the IPL 2026 playoffs. Win probabilities, NRR strategy, match-by-match roadmap.`;

  try {
    const API_URL =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${API_URL}/api/simulate`, {
      method: "POST",
      next: { revalidate: 300 },
    });
    if (res.ok) {
      const data = await res.json();
      const result = data.results?.find(
        (r: { team: string }) => r.team === teamKey
      );
      if (result) {
        description = `${teamData.name}: ${result.top4_pct}% Top 4, ${result.top2_pct}% Top 2, ${result.title_pct}% Title. Based on 50,000 simulations.`;
      }
    }
  } catch {
    // Fall back to static description
  }

  return {
    title: `${teamData.short} Win Path`,
    description,
    openGraph: {
      title: `${teamData.name} | Win Path`,
      description,
    },
    twitter: {
      card: "summary_large_image",
      title: `${teamData.name} | Win Path`,
      description,
    },
  };
}

export default function TeamLayout({ children }: Props) {
  return children;
}
