from sqlalchemy import Column, String, Text, Integer, Boolean, Date, Time, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class Tournament(Base):
    __tablename__ = "tournaments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    sport_type = Column(String(100), default="basketball")
    start_date = Column(Date)
    end_date = Column(Date)
    max_teams = Column(Integer, default=16)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    teams = relationship("Team", back_populates="tournament", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="tournament", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="tournament", cascade="all, delete-orphan")

class Court(Base):
    __tablename__ = "courts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    location = Column(String(255))
    capacity = Column(Integer, default=20)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    matches = relationship("Match", back_populates="court")

class TimeSlot(Base):
    __tablename__ = "time_slots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    day_of_week = Column(Integer, nullable=False)  # 0=Sunday, 1=Monday, etc.
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    matches = relationship("Match", back_populates="time_slot")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('day_of_week >= 0 AND day_of_week <= 6', name='valid_day_of_week'),
        UniqueConstraint('day_of_week', 'start_time', name='unique_day_time'),
    )

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id"), nullable=False)
    name = Column(String(255), nullable=False)
    captain_name = Column(String(255))
    captain_email = Column(String(255))
    captain_phone = Column(String(50))
    earliest_start_time = Column(Time, default=func.time('09:00:00'))
    latest_start_time = Column(Time, default=func.time('22:00:00'))
    preferred_days = Column(ARRAY(Integer), default=[1, 2, 3, 4, 5])  # Monday to Friday
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    tournament = relationship("Tournament", back_populates="teams")
    team1_matches = relationship("Match", foreign_keys="Match.team1_id", back_populates="team1")
    team2_matches = relationship("Match", foreign_keys="Match.team2_id", back_populates="team2")
    restrictions = relationship("TeamRestriction", back_populates="team", cascade="all, delete-orphan")

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id"), nullable=False)
    team1_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    team2_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    court_id = Column(UUID(as_uuid=True), ForeignKey("courts.id"))
    time_slot_id = Column(UUID(as_uuid=True), ForeignKey("time_slots.id"))
    scheduled_date = Column(Date)
    scheduled_time = Column(Time)
    status = Column(String(50), default="scheduled")  # scheduled, completed, cancelled
    score_team1 = Column(Integer, default=0)
    score_team2 = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    tournament = relationship("Tournament", back_populates="matches")
    team1 = relationship("Team", foreign_keys=[team1_id], back_populates="team1_matches")
    team2 = relationship("Team", foreign_keys=[team2_id], back_populates="team2_matches")
    court = relationship("Court", back_populates="matches")
    time_slot = relationship("TimeSlot", back_populates="matches")
    schedule_matches = relationship("ScheduleMatch", back_populates="match")

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id"), nullable=False)
    week_start_date = Column(Date, nullable=False)
    week_end_date = Column(Date, nullable=False)
    status = Column(String(50), default="draft")  # draft, published, archived
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    tournament = relationship("Tournament", back_populates="schedules")
    schedule_matches = relationship("ScheduleMatch", back_populates="schedule")

class ScheduleMatch(Base):
    __tablename__ = "schedule_matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("schedules.id"), nullable=False)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    schedule = relationship("Schedule", back_populates="schedule_matches")
    match = relationship("Match", back_populates="schedule_matches")

class TeamRestriction(Base):
    __tablename__ = "team_restrictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    restriction_date = Column(Date, nullable=False)  # The Saturday date this restriction applies to
    restriction_type = Column(String(50), nullable=False)  # 'not_scheduled', 'time_preference', 'court_preference', 'tournament_time_preference'
    restriction_value = Column(Text)  # JSON string with specific constraints
    notes = Column(Text)  # Additional notes from organizer
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="restrictions")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('team_id', 'restriction_date', 'restriction_type', name='unique_team_restriction'),
    )

class TournamentRound(Base):
    __tablename__ = "tournament_rounds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id"), nullable=False)
    round_number = Column(Integer, nullable=False)  # 1, 2, 3, 4, 5
    round_name = Column(String(100), nullable=False)  # 'Primera Ronda', 'Segunda Ronda', etc.
    round_type = Column(String(50), nullable=False)  # 'group_stage', 'knockout', 'final'
    status = Column(String(50), default="pending")  # 'pending', 'in_progress', 'completed'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    tournament = relationship("Tournament")
    groups = relationship("TournamentGroup", back_populates="round", cascade="all, delete-orphan")
    fixtures = relationship("TournamentFixture", back_populates="round", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('tournament_id', 'round_number', name='unique_tournament_round'),
    )

class TournamentGroup(Base):
    __tablename__ = "tournament_groups"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_round_id = Column(UUID(as_uuid=True), ForeignKey("tournament_rounds.id"), nullable=False)
    group_name = Column(String(50), nullable=False)  # 'Grupo A', 'Grupo B'
    group_order = Column(Integer, nullable=False)  # 1, 2
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    round = relationship("TournamentRound", back_populates="groups")
    fixtures = relationship("TournamentFixture", back_populates="group", cascade="all, delete-orphan")
    standings = relationship("TournamentStanding", back_populates="group", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('tournament_round_id', 'group_name', name='unique_round_group'),
    )

class TournamentFixture(Base):
    __tablename__ = "tournament_fixtures"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_round_id = Column(UUID(as_uuid=True), ForeignKey("tournament_rounds.id"), nullable=False)
    tournament_group_id = Column(UUID(as_uuid=True), ForeignKey("tournament_groups.id"), nullable=True)
    team1_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    team2_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=True)
    fixture_type = Column(String(50), nullable=False)  # 'group_match', 'semifinal', 'third_place', 'final', 'regular'
    match_order = Column(Integer)  # Order within the round/group
    team1_score = Column(Integer, default=0)
    team2_score = Column(Integer, default=0)
    status = Column(String(50), default="pending")  # 'pending', 'scheduled', 'completed'
    last_updated_by = Column(String(255), nullable=True)  # Who last updated the scores
    last_updated_at = Column(DateTime(timezone=True), nullable=True)  # When scores were last updated
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    round = relationship("TournamentRound", back_populates="fixtures")
    group = relationship("TournamentGroup", back_populates="fixtures")
    team1 = relationship("Team", foreign_keys=[team1_id])
    team2 = relationship("Team", foreign_keys=[team2_id])
    match = relationship("Match")

class TournamentStanding(Base):
    __tablename__ = "tournament_standings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_group_id = Column(UUID(as_uuid=True), ForeignKey("tournament_groups.id"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    matches_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    points_for = Column(Integer, default=0)
    points_against = Column(Integer, default=0)
    points_difference = Column(Integer, default=0)
    points = Column(Integer, default=0)  # Tournament points (2 for win, 1 for loss, 0 for forfeit)
    position = Column(Integer)  # Final position in group
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    group = relationship("TournamentGroup", back_populates="standings")
    team = relationship("Team")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('tournament_group_id', 'team_id', name='unique_group_team'),
    )
