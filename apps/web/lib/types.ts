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

export interface MatchImpactTeam {
  team: string;
  if_team1_wins: number;
  if_team2_wins: number;
  most_affected: boolean;
}

export interface ImpactMatch {
  id: string;
  team1: string;
  team2: string;
  date: string;
  venue: string;
  team1_win_pct: number;
  team2_win_pct: number;
}

export interface ImpactResponse {
  match: ImpactMatch;
  baseline: SimulationTeamResult[];
  if_team1_wins: SimulationTeamResult[];
  if_team2_wins: SimulationTeamResult[];
  impact: MatchImpactTeam[];
  simulations_run: number;
  generated_at: string;
}

export interface ScenarioOutcome {
  match_id: string;
  winner: string;
}

export interface ScenarioDelta {
  team: string;
  top4_delta: number;
  top2_delta: number;
  title_delta: number;
}

export interface ScenarioResponse {
  results: SimulationTeamResult[];
  baseline: SimulationTeamResult[];
  deltas: ScenarioDelta[];
  forced_count: number;
  simulations_run: number;
  generated_at: string;
}

export interface WinPathMatch {
  id: string;
  match_number: number;
  date: string;
  time: string;
  opponent: string;
  venue: string;
  venue_name: string;
  venue_city: string;
  is_home: boolean;
  status: "completed" | "upcoming";
  result: "won" | "lost" | null;
  score: string | null;
  win_prob: number | null;
  impact: number | null;
  classification: "MUST_WIN" | "FAVORED" | "TOSS_UP" | "TOUGH" | "UPSET_NEEDED" | null;
}

export interface WinPathSummary {
  matches_played: number;
  matches_remaining: number;
  wins: number;
  losses: number;
  must_wins: number;
  favored: number;
  toss_ups: number;
  tough: number;
  upset_needed: number;
}

export interface WinPathResponse {
  team: string;
  team_top4_pct: number;
  matches: WinPathMatch[];
  summary: WinPathSummary;
  generated_at: string;
}
