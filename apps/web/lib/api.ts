import type { StandingsResponse, SimulateResponse, ScheduleResponse, ImpactResponse, ScenarioOutcome, ScenarioResponse, WinPathResponse, NRRStrategyResponse, MatchDetailResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

export async function getStandings(): Promise<StandingsResponse> {
  const res = await fetch(`${API_URL}/api/standings`);
  if (!res.ok) throw new Error(`Standings API error: ${res.status}`);
  return res.json();
}

export async function simulate(): Promise<SimulateResponse> {
  const res = await fetch(`${API_URL}/api/simulate`, { method: "POST" });
  if (!res.ok) throw new Error(`Simulate API error: ${res.status}`);
  return res.json();
}

export async function getSchedule(team?: string, status?: string): Promise<ScheduleResponse> {
  const params = new URLSearchParams();
  if (team) params.set("team", team);
  if (status) params.set("status", status);
  const qs = params.toString() ? `?${params.toString()}` : "";
  const res = await fetch(`${API_URL}/api/schedule${qs}`);
  if (!res.ok) throw new Error(`Schedule API error: ${res.status}`);
  return res.json();
}

export async function getImpact(matchId: string): Promise<ImpactResponse> {
  const res = await fetch(`${API_URL}/api/impact`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ match_id: matchId }),
  });
  if (!res.ok) throw new Error(`Impact API error: ${res.status}`);
  return res.json();
}

export async function runScenario(outcomes: ScenarioOutcome[]): Promise<ScenarioResponse> {
  const res = await fetch(`${API_URL}/api/scenario`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ outcomes }),
  });
  if (!res.ok) throw new Error(`Scenario API error: ${res.status}`);
  return res.json();
}

export async function getWinPath(team: string): Promise<WinPathResponse> {
  const res = await fetch(`${API_URL}/api/winpath/${team}`);
  if (!res.ok) throw new Error(`WinPath API error: ${res.status}`);
  return res.json();
}

export async function getNRRStrategy(team: string): Promise<NRRStrategyResponse> {
  const res = await fetch(`${API_URL}/api/nrr-strategy/${team}`);
  if (!res.ok) throw new Error(`NRR Strategy API error: ${res.status}`);
  return res.json();
}

export async function getMatchDetail(matchId: string, team: string): Promise<MatchDetailResponse> {
  const res = await fetch(`${API_URL}/api/match-detail/${matchId}/${team}`);
  if (!res.ok) throw new Error(`Match detail API error: ${res.status}`);
  return res.json();
}
