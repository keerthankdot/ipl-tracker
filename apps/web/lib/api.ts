import type { StandingsResponse, SimulateResponse, ScheduleResponse } from "./types";

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

export async function getSchedule(team?: string): Promise<ScheduleResponse> {
  const params = team ? `?team=${team}` : "";
  const res = await fetch(`${API_URL}/api/schedule${params}`);
  if (!res.ok) throw new Error(`Schedule API error: ${res.status}`);
  return res.json();
}
