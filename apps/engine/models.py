from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel

TeamKey = Literal["RCB", "CSK", "MI", "KKR", "SRH", "RR", "DC", "PBKS", "GT", "LSG"]


class MatchStatus(str, Enum):
    COMPLETED = "completed"
    UPCOMING = "upcoming"
    LIVE = "live"
    NO_RESULT = "no_result"
    PLAYOFF_PENDING = "playoff_pending"


class Match(BaseModel):
    id: str
    match_number: int
    date: str
    time: str
    team1: Optional[TeamKey] = None
    team2: Optional[TeamKey] = None
    venue: str
    status: MatchStatus
    winner: Optional[TeamKey] = None
    bat_first: Optional[TeamKey] = None
    score_team1: Optional[str] = None
    overs_team1: Optional[str] = None
    score_team2: Optional[str] = None
    overs_team2: Optional[str] = None


class TeamStanding(BaseModel):
    team: TeamKey
    played: int = 0
    won: int = 0
    lost: int = 0
    no_result: int = 0
    points: int = 0
    nrr: float = 0.0
    total_runs_scored: int = 0
    total_overs_faced: float = 0.0
    total_runs_conceded: int = 0
    total_overs_bowled: float = 0.0


class SimulationResult(BaseModel):
    team: TeamKey
    top4_pct: float
    top2_pct: float
    title_pct: float


class Venue(BaseModel):
    key: str
    name: str
    city: str
    capacity: Optional[int] = None
    avg_1st_innings: int
    avg_2nd_innings: int
    bat_first_win_pct: int
    chase_win_pct: int
    pace_wicket_pct: int
    spin_wicket_pct: int
    dew_factor: str
    altitude_m: Optional[int] = None
    boundary_avg_m: Optional[int] = None
    notes: str = ""


class SimulateResponse(BaseModel):
    results: list[SimulationResult]
    simulations_run: int
    elapsed_seconds: float
    based_on_matches: int
    generated_at: datetime
