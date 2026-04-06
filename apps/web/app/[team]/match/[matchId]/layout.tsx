import type { Metadata } from "next";
import { TEAMS } from "@/lib/teams";

type Props = {
  params: Promise<{ team: string; matchId: string }>;
  children: React.ReactNode;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { team, matchId } = await params;
  const teamKey = team.toUpperCase();
  const teamData = TEAMS[teamKey as keyof typeof TEAMS];

  if (!teamData) {
    return { title: "Match Not Found" };
  }

  let title = `${teamData.short} Match ${matchId} | Win Path`;
  let description = `${teamData.name} match analysis. Venue intelligence, win probability, toss analysis, player form.`;

  try {
    const API_URL =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(
      `${API_URL}/api/match-detail/${matchId}/${team}`,
      { next: { revalidate: 300 } }
    );
    if (res.ok) {
      const data = await res.json();
      title = `${teamData.short} vs ${data.opponent}`;
      const winPct = data.win_prob
        ? `${Math.round(data.win_prob * 100)}% win probability.`
        : "";
      const classTag = data.classification
        ? ` ${data.classification.replace("_", " ")}.`
        : "";
      description = `${teamData.short} vs ${data.opponent}, ${data.date} at ${data.venue?.name || "TBD"}. ${winPct}${classTag}`;
    }
  } catch {
    // Fall back to generic
  }

  return {
    title,
    description,
    openGraph: {
      title: `${title} | Win Path`,
      description,
    },
    twitter: {
      card: "summary_large_image",
      title: `${title} | Win Path`,
      description,
    },
  };
}

export default function MatchLayout({ children }: Props) {
  return children;
}
