from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union
from datetime import date, time, datetime
from uuid import UUID

# Base schemas
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            date: lambda v: v.isoformat() if v else None,
            time: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat() if v else None,
        }

# Tournament schemas
class TournamentBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    sport_type: str = Field(default="basketball", max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    max_teams: int = Field(default=16, ge=2, le=100)

class TournamentCreate(TournamentBase):
    pass

class TournamentUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    sport_type: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    max_teams: Optional[int] = Field(None, ge=2, le=100)

class TournamentResponse(TournamentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

# Court schemas
class CourtBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    location: Optional[str] = None
    capacity: int = Field(default=20, ge=1, le=1000)
    is_active: bool = Field(default=True)

class CourtCreate(CourtBase):
    pass

class CourtUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    location: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=1, le=1000)
    is_active: Optional[bool] = None

class CourtResponse(CourtBase):
    id: UUID
    created_at: datetime

# Time slot schemas
class TimeSlotBase(BaseSchema):
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Sunday, 1=Monday, etc.
    start_time: time
    end_time: time
    is_active: bool = Field(default=True)

    @validator('end_time')
    def end_time_after_start_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

class TimeSlotCreate(TimeSlotBase):
    pass

class TimeSlotUpdate(BaseSchema):
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_active: Optional[bool] = None

class TimeSlotResponse(TimeSlotBase):
    id: UUID
    created_at: datetime

# Team schemas
class TeamBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    captain_name: Optional[str] = Field(None, max_length=255)
    captain_email: Optional[str] = Field(None, max_length=255)
    captain_phone: Optional[str] = Field(None, max_length=50)
    earliest_start_time: time = Field(default=time(9, 0))
    latest_start_time: time = Field(default=time(22, 0))
    preferred_days: List[int] = Field(default=[1, 2, 3, 4, 5])  # Monday to Friday
    is_active: bool = Field(default=True)

    @validator('preferred_days')
    def validate_preferred_days(cls, v):
        for day in v:
            if day < 0 or day > 6:
                raise ValueError('preferred_days must be between 0 and 6')
        return v

    @validator('latest_start_time')
    def latest_time_after_earliest(cls, v, values):
        if 'earliest_start_time' in values and v <= values['earliest_start_time']:
            raise ValueError('latest_start_time must be after earliest_start_time')
        return v

class TeamCreate(TeamBase):
    tournament_id: UUID

class TeamUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    captain_name: Optional[str] = Field(None, max_length=255)
    captain_email: Optional[str] = Field(None, max_length=255)
    captain_phone: Optional[str] = Field(None, max_length=50)
    earliest_start_time: Optional[time] = None
    latest_start_time: Optional[time] = None
    preferred_days: Optional[List[int]] = None
    is_active: Optional[bool] = None

class TeamResponse(TeamBase):
    id: UUID
    tournament_id: UUID
    created_at: datetime
    updated_at: datetime

# Match schemas
class MatchBase(BaseSchema):
    team1_id: UUID
    team2_id: UUID
    court_id: Optional[UUID] = None
    time_slot_id: Optional[UUID] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None
    status: str = Field(default="scheduled", max_length=50)
    score_team1: int = Field(default=0, ge=0)
    score_team2: int = Field(default=0, ge=0)

    @validator('team2_id')
    def teams_must_be_different(cls, v, values):
        if 'team1_id' in values and v == values['team1_id']:
            raise ValueError('team1_id and team2_id must be different')
        return v

class MatchCreate(MatchBase):
    tournament_id: UUID

class MatchUpdate(BaseSchema):
    court_id: Optional[UUID] = None
    time_slot_id: Optional[UUID] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None
    status: Optional[str] = Field(None, max_length=50)
    score_team1: Optional[int] = Field(None, ge=0)
    score_team2: Optional[int] = Field(None, ge=0)

class MatchResponse(MatchBase):
    id: UUID
    tournament_id: UUID
    created_at: datetime
    updated_at: datetime

# Schedule schemas
class ScheduleBase(BaseSchema):
    week_start_date: date
    week_end_date: date
    status: str = Field(default="draft", max_length=50)

    @validator('week_end_date')
    def end_date_after_start_date(cls, v, values):
        if 'week_start_date' in values and v < values['week_start_date']:
            raise ValueError('week_end_date must be after or equal to week_start_date')
        return v

class ScheduleCreate(ScheduleBase):
    tournament_id: UUID

class ScheduleUpdate(BaseSchema):
    week_start_date: Optional[date] = None
    week_end_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=50)

class ScheduleResponse(ScheduleBase):
    id: UUID
    tournament_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

# Scheduler schemas
class SchedulerRequest(BaseSchema):
    tournament_id: UUID
    week_start_date: date
    week_end_date: date
    max_matches_per_team_per_week: int = Field(default=2, ge=1, le=5)
    fairness_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    court_utilization_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    team_preference_weight: float = Field(default=0.3, ge=0.0, le=1.0)

class SchedulerResponse(BaseSchema):
    schedule_id: UUID
    tournament_id: Optional[UUID] = None  # Make this optional
    week_start_date: date
    week_end_date: date
    total_matches: int
    total_courts_used: int
    total_time_slots_used: int
    fairness_score: float
    court_utilization_score: float
    team_preference_score: float
    processing_time_seconds: float
    status: str
    message: str

# Export schemas
class ExportRequest(BaseSchema):
    schedule_id: UUID
    format: str = Field(..., pattern="^(json|csv|excel|pdf)$")

class ExportResponse(BaseSchema):
    download_url: str
    filename: str
    format: str
    file_size_bytes: int

# List response schemas
class TournamentListResponse(BaseSchema):
    tournaments: List[TournamentResponse]
    total: int
    page: int
    size: int

class TeamListResponse(BaseSchema):
    teams: List[TeamResponse]
    total: int
    page: int
    size: int

class MatchListResponse(BaseSchema):
    matches: List[MatchResponse]
    total: int
    page: int
    size: int

class ScheduleListResponse(BaseSchema):
    schedules: List[ScheduleResponse]
    total: int
    page: int
    size: int

# Team Restriction schemas
class TeamRestrictionBase(BaseSchema):
    restriction_date: date
    restriction_type: str = Field(..., pattern="^(not_scheduled|time_preference|time_after|time_before|time_range|court_preference|tournament_time_preference)$")
    restriction_value: Optional[str] = None  # JSON string with specific constraints
    notes: Optional[str] = None

class TeamRestrictionCreate(TeamRestrictionBase):
    team_id: UUID

class TeamRestrictionUpdate(BaseSchema):
    restriction_type: Optional[str] = Field(None, pattern="^(not_scheduled|time_preference|time_after|time_before|time_range|court_preference|tournament_time_preference)$")
    restriction_value: Optional[str] = None
    notes: Optional[str] = None

class TeamRestrictionResponse(TeamRestrictionBase):
    id: UUID
    team_id: UUID
    created_at: datetime
    updated_at: datetime

class TeamRestrictionListResponse(BaseSchema):
    restrictions: List[TeamRestrictionResponse]
    total: int
    page: int
    size: int

# Tournament Fixture schemas
class TournamentRoundBase(BaseSchema):
    round_number: int = Field(..., ge=1, le=5)
    round_name: str = Field(..., max_length=100)
    round_type: str = Field(..., pattern="^(group_stage|knockout|final)$")
    status: str = Field(default="pending", pattern="^(pending|in_progress|completed)$")

class TournamentRoundCreate(TournamentRoundBase):
    tournament_id: UUID

class TournamentRoundUpdate(BaseSchema):
    round_name: Optional[str] = Field(None, max_length=100)
    round_type: Optional[str] = Field(None, pattern="^(group_stage|knockout|final)$")
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed)$")

class TournamentRoundResponse(TournamentRoundBase):
    id: UUID
    tournament_id: UUID
    created_at: datetime
    updated_at: datetime

class TournamentGroupBase(BaseSchema):
    group_name: str = Field(..., max_length=50)
    group_order: int = Field(..., ge=1, le=2)

class TournamentGroupCreate(TournamentGroupBase):
    tournament_round_id: UUID

class TournamentGroupResponse(TournamentGroupBase):
    id: UUID
    tournament_round_id: UUID
    created_at: datetime

class TournamentFixtureBase(BaseSchema):
    team1_id: Optional[UUID] = None
    team2_id: Optional[UUID] = None
    fixture_type: str = Field(..., pattern="^(group_match|semifinal|third_place|final|regular)$")
    match_order: Optional[int] = None
    team1_score: int = Field(default=0, ge=0)
    team2_score: int = Field(default=0, ge=0)
    status: str = Field(default="pending", pattern="^(pending|scheduled|completed)$")
    last_updated_by: Optional[str] = Field(None, max_length=255)
    last_updated_at: Optional[datetime] = None

    @validator('team2_id')
    def teams_must_be_different(cls, v, values):
        if 'team1_id' in values and v is not None and values['team1_id'] is not None and v == values['team1_id']:
            raise ValueError('team1_id and team2_id must be different')
        return v

class TournamentFixtureCreate(TournamentFixtureBase):
    tournament_round_id: UUID
    tournament_group_id: Optional[UUID] = None

class TournamentFixtureUpdate(BaseSchema):
    team1_score: Optional[int] = Field(None, ge=0)
    team2_score: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern="^(pending|scheduled|completed)$")
    match_id: Optional[UUID] = None
    last_updated_by: Optional[str] = Field(None, max_length=255)
    last_updated_at: Optional[datetime] = None

class TournamentFixtureResponse(TournamentFixtureBase):
    id: UUID
    tournament_round_id: UUID
    tournament_group_id: Optional[UUID] = None
    match_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

class TournamentStandingBase(BaseSchema):
    matches_played: int = Field(default=0, ge=0)
    wins: int = Field(default=0, ge=0)
    losses: int = Field(default=0, ge=0)
    points_for: int = Field(default=0, ge=0)
    points_against: int = Field(default=0, ge=0)
    points_difference: int = Field(default=0)
    points: int = Field(default=0, ge=0)  # Tournament points (2 for win, 1 for loss, 0 for forfeit)
    position: Optional[int] = Field(None, ge=1)

class TournamentStandingCreate(TournamentStandingBase):
    tournament_group_id: UUID
    team_id: UUID

class TournamentStandingUpdate(BaseSchema):
    matches_played: Optional[int] = Field(None, ge=0)
    wins: Optional[int] = Field(None, ge=0)
    losses: Optional[int] = Field(None, ge=0)
    points_for: Optional[int] = Field(None, ge=0)
    points_against: Optional[int] = Field(None, ge=0)
    points_difference: Optional[int] = None
    position: Optional[int] = Field(None, ge=1)

class TournamentStandingResponse(TournamentStandingBase):
    id: UUID
    tournament_group_id: UUID
    team_id: UUID
    created_at: datetime
    updated_at: datetime

# List response schemas
class TournamentRoundListResponse(BaseSchema):
    rounds: List[TournamentRoundResponse]
    total: int
    page: int
    size: int

class TournamentGroupListResponse(BaseSchema):
    groups: List[TournamentGroupResponse]
    total: int
    page: int
    size: int

class TournamentFixtureListResponse(BaseSchema):
    fixtures: List[TournamentFixtureResponse]
    total: int
    page: int
    size: int

class TournamentStandingListResponse(BaseSchema):
    standings: List[TournamentStandingResponse]
    total: int
    page: int
    size: int
