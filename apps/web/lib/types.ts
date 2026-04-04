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

export interface MatchDetailVenue {
  name: string;
  city: string;
  capacity: number | null;
  avg_1st_innings: number;
  avg_2nd_innings: number;
  bat_first_win_pct: number;
  chase_win_pct: number;
  pace_wicket_pct: number;
  spin_wicket_pct: number;
  dew_factor: string;
  altitude_m: number | null;
  boundary_avg_m: number | null;
  notes: string;
}

export interface MatchDetailToss {
  bat_first_win_pct: number;
  chase_win_pct: number;
  recommendation: string;
  dew_factor: string;
}

export interface MatchDetailH2H {
  my_wins: number;
  opponent_wins: number;
  total: number;
  my_win_pct: number;
}

export interface DewPrediction {
  level: "heavy" | "moderate" | "light" | "none";
  impact: string;
  is_evening_match: boolean;
}

export interface WeatherData {
  temperature_c: number;
  humidity_pct: number;
  wind_speed_kmh: number;
  wind_direction_deg: number;
  rain_probability_pct: number;
  rain_mm: number;
  cloud_cover_pct: number;
  description: string;
  dew: DewPrediction;
  forecast_for: string;
}

export interface MatchDetailResponse {
  match_id: string;
  team: string;
  opponent: string;
  date: string;
  time: string;
  status: string;
  is_home: boolean;
  win_prob: number | null;
  classification: string | null;
  impact: { impact_pct: number; team_top4_pct: number } | null;
  result: {
    result: string;
    score_team1: string;
    overs_team1: string;
    score_team2: string;
    overs_team2: string;
    winner: string;
  } | null;
  venue: MatchDetailVenue;
  toss: MatchDetailToss;
  h2h: MatchDetailH2H;
  weather: WeatherData | null;
  players: MatchPlayers | null;
  generated_at: string;
}

export interface PlayerBattingSummary {
  innings: number;
  total_runs: number;
  avg: number;
  strike_rate: number;
}

export interface PlayerBowlingSummary {
  innings: number;
  wickets: number;
  economy: number;
  avg: number | null;
}

export interface PlayerForm {
  id: string;
  name: string;
  team: string;
  role: "batter" | "bowler" | "allrounder";
  matches_played: number;
  summary: {
    batting: PlayerBattingSummary | null;
    bowling: PlayerBowlingSummary | null;
  };
}

export interface MatchPlayers {
  team1_players: PlayerForm[];
  team2_players: PlayerForm[];
}

export interface NRRScenarioBatChase {
  description: string;
  min_margin_runs?: number;
  max_overs?: string;
  resulting_nrr: number;
}

export interface NRRScenario {
  target: string;
  target_team?: string;
  target_nrr?: number;
  bat_first?: NRRScenarioBatChase;
  chase?: NRRScenarioBatChase;
  feasibility?: string;
  description?: string;
  worst_case_nrr?: number;
  resulting_rank?: number;
}

export interface NRRStrategyResponse {
  team: string;
  current_nrr: number;
  nrr_rank: number;
  next_match: {
    id: string;
    opponent: string;
    venue: string;
    venue_avg_1st: number;
  };
  scenarios: NRRScenario[];
  generated_at: string;
}
