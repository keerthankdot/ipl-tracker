export interface TeamStanding {
  rank: number;
  team: string;
  played: number;
  won: number;
  lost: number;
  no_result: number;
  points: number;
  nrr: number;
}

export interface StandingsResponse {
  standings: TeamStanding[];
  last_updated: string;
  matches_completed: number;
  matches_remaining: number;
}

export interface SimulationTeamResult {
  team: string;
  top4_pct: number;
  top2_pct: number;
  title_pct: number;
}

export interface SimulateResponse {
  results: SimulationTeamResult[];
  simulations_run: number;
  elapsed_seconds: number;
  based_on_matches: number;
  generated_at: string;
  cached: boolean;
}

export interface Match {
  id: string;
  match_number: number;
  date: string;
  time: string;
  team1: string;
  team2: string;
  venue: string;
  status: string;
  winner?: string;
  bat_first?: string;
  score_team1?: string;
  overs_team1?: string;
  score_team2?: string;
  overs_team2?: string;
}

export interface ScheduleResponse {
  matches: Match[];
  total: number;
  filtered: number;
}
