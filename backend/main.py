from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date, timedelta, time, datetime
import uuid

from app.database import get_db, init_db
from app.models import (
    Tournament, Team, Court, TimeSlot, Match, Schedule, ScheduleMatch, TeamRestriction,
    TournamentRound, TournamentGroup, TournamentFixture, TournamentStanding
)
from app.schemas import (
    TournamentCreate, TournamentUpdate, TournamentResponse, TournamentListResponse,
    TeamCreate, TeamUpdate, TeamResponse, TeamListResponse,
    MatchCreate, MatchUpdate, MatchResponse, MatchListResponse,
    ScheduleCreate, ScheduleUpdate, ScheduleResponse, ScheduleListResponse,
    SchedulerRequest, SchedulerResponse, ExportRequest, ExportResponse,
    TeamRestrictionCreate, TeamRestrictionUpdate, TeamRestrictionResponse, TeamRestrictionListResponse,
    TournamentRoundCreate, TournamentRoundUpdate, TournamentRoundResponse, TournamentRoundListResponse,
    TournamentGroupCreate, TournamentGroupResponse, TournamentGroupListResponse,
    TournamentFixtureCreate, TournamentFixtureUpdate, TournamentFixtureResponse, TournamentFixtureListResponse,
    TournamentStandingCreate, TournamentStandingUpdate, TournamentStandingResponse, TournamentStandingListResponse
)
from app.scheduler import SportifyScheduler
from app.tournament_generator import TournamentFixtureGenerator


# Initialize FastAPI app
app = FastAPI(
    title="Sportify API",
    description="Automated Sports Tournament Scheduling Platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Sportify API is running"}

# Tournament endpoints
@app.get("/tournaments", response_model=TournamentListResponse)
async def get_tournaments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all tournaments"""
    tournaments = db.query(Tournament).offset(skip).limit(limit).all()
    return TournamentListResponse(
        tournaments=[TournamentResponse.from_orm(t) for t in tournaments],
        total=len(tournaments),
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@app.get("/tournaments/{tournament_id}", response_model=TournamentResponse)
async def get_tournament(tournament_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific tournament"""
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return TournamentResponse.from_orm(tournament)

@app.post("/tournaments", response_model=TournamentResponse)
async def create_tournament(tournament: TournamentCreate, db: Session = Depends(get_db)):
    """Create a new tournament"""
    db_tournament = Tournament(**tournament.dict())
    db.add(db_tournament)
    db.commit()
    db.refresh(db_tournament)
    return TournamentResponse.from_orm(db_tournament)

@app.put("/tournaments/{tournament_id}", response_model=TournamentResponse)
async def update_tournament(
    tournament_id: uuid.UUID,
    tournament: TournamentUpdate,
    db: Session = Depends(get_db)
):
    """Update a tournament"""
    db_tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not db_tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    for field, value in tournament.dict(exclude_unset=True).items():
        setattr(db_tournament, field, value)
    
    db.commit()
    db.refresh(db_tournament)
    return TournamentResponse.from_orm(db_tournament)

@app.delete("/tournaments/{tournament_id}")
async def delete_tournament(tournament_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a tournament"""
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    db.delete(tournament)
    db.commit()
    return {"message": "Tournament deleted successfully"}

# Team endpoints
@app.get("/teams", response_model=TeamListResponse)
async def get_teams(
    tournament_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all teams, optionally filtered by tournament"""
    query = db.query(Team)
    if tournament_id:
        query = query.filter(Team.tournament_id == tournament_id)
    
    teams = query.offset(skip).limit(limit).all()
    return TeamListResponse(
        teams=[TeamResponse.from_orm(t) for t in teams],
        total=len(teams),
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@app.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(team_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific team"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return TeamResponse.from_orm(team)

@app.post("/teams", response_model=TeamResponse)
async def create_team(team: TeamCreate, db: Session = Depends(get_db)):
    """Create a new team"""
    db_team = Team(**team.dict())
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return TeamResponse.from_orm(db_team)

@app.put("/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: uuid.UUID,
    team: TeamUpdate,
    db: Session = Depends(get_db)
):
    """Update a team"""
    db_team = db.query(Team).filter(Team.id == team_id).first()
    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    for field, value in team.dict(exclude_unset=True).items():
        setattr(db_team, field, value)
    
    db.commit()
    db.refresh(db_team)
    return TeamResponse.from_orm(db_team)

@app.delete("/teams/{team_id}")
async def delete_team(team_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a team"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    db.delete(team)
    db.commit()
    return {"message": "Team deleted successfully"}

# Court endpoints
@app.get("/courts")
async def get_courts(db: Session = Depends(get_db)):
    """Get all courts"""
    courts = db.query(Court).all()
    return [{"id": str(c.id), "name": c.name, "location": c.location} for c in courts]

@app.get("/courts/{court_id}")
async def get_court(court_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific court"""
    court = db.query(Court).filter(Court.id == court_id).first()
    if not court:
        raise HTTPException(status_code=404, detail="Court not found")
    return {"id": str(court.id), "name": court.name, "location": court.location}

# Time slot endpoints
@app.get("/time-slots")
async def get_time_slots(db: Session = Depends(get_db)):
    """Get all time slots"""
    time_slots = db.query(TimeSlot).all()
    return [{"id": str(ts.id), "start_time": ts.start_time, "end_time": ts.end_time} for ts in time_slots]

@app.get("/time-slots/{time_slot_id}")
async def get_time_slot(time_slot_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific time slot"""
    time_slot = db.query(TimeSlot).filter(TimeSlot.id == time_slot_id).first()
    if not time_slot:
        raise HTTPException(status_code=404, detail="Time slot not found")
    return {"id": str(time_slot.id), "start_time": time_slot.start_time, "end_time": time_slot.end_time}

# Match endpoints
@app.get("/matches", response_model=MatchListResponse)
async def get_matches(
    tournament_id: Optional[uuid.UUID] = None,
    scheduled_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all matches, optionally filtered by tournament or date"""
    query = db.query(Match)
    if tournament_id:
        query = query.join(Team, Match.team1_id == Team.id).filter(Team.tournament_id == tournament_id)
    if scheduled_date:
        query = query.filter(Match.scheduled_date == scheduled_date)
    
    matches = query.offset(skip).limit(limit).all()
    return MatchListResponse(
        matches=[MatchResponse.from_orm(m) for m in matches],
        total=len(matches),
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@app.get("/matches/{match_id}", response_model=MatchResponse)
async def get_match(match_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific match"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return MatchResponse.from_orm(match)

@app.post("/matches", response_model=MatchResponse)
async def create_match(match: MatchCreate, db: Session = Depends(get_db)):
    """Create a new match"""
    db_match = Match(**match.dict())
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return MatchResponse.from_orm(db_match)

@app.put("/matches/{match_id}", response_model=MatchResponse)
async def update_match(
    match_id: uuid.UUID,
    match: MatchUpdate,
    db: Session = Depends(get_db)
):
    """Update a match"""
    db_match = db.query(Match).filter(Match.id == match_id).first()
    if not db_match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    for field, value in match.dict(exclude_unset=True).items():
        setattr(db_match, field, value)
    
    db.commit()
    db.refresh(db_match)
    return MatchResponse.from_orm(db_match)

@app.delete("/matches/{match_id}")
async def delete_match(match_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a match"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    db.delete(match)
    db.commit()
    return {"message": "Match deleted successfully"}

# Schedule endpoints
@app.get("/schedules", response_model=ScheduleListResponse)
async def get_schedules(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all schedules"""
    schedules = db.query(Schedule).offset(skip).limit(limit).all()
    return ScheduleListResponse(
        schedules=[ScheduleResponse.from_orm(s) for s in schedules],
        total=len(schedules),
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@app.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific schedule"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return ScheduleResponse.from_orm(schedule)

@app.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db)):
    """Create a new schedule"""
    db_schedule = Schedule(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return ScheduleResponse.from_orm(db_schedule)

@app.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: uuid.UUID,
    schedule: ScheduleUpdate,
    db: Session = Depends(get_db)
):
    """Update a schedule"""
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    for field, value in schedule.dict(exclude_unset=True).items():
        setattr(db_schedule, field, value)
    
    db.commit()
    db.refresh(db_schedule)
    return ScheduleResponse.from_orm(db_schedule)

@app.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a schedule"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    db.delete(schedule)
    db.commit()
    return {"message": "Schedule deleted successfully"}

# Scheduler endpoints
@app.post("/scheduler/saturday")
async def create_saturday_schedule(
    request_date: date = Query(..., description="Date for Saturday schedule"),
    db: Session = Depends(get_db)
):
    """Create Saturday schedule for all tournaments"""
    try:
        scheduler = SportifyScheduler(db)
        result = scheduler.create_saturday_schedule(request_date)
        
        # The scheduler returns a SchedulerResponse object
        # Convert it to a dictionary response for the frontend
        return {
            "success": True,
            "message": f"Saturday schedule created successfully! {result.total_matches} matches scheduled across all tournaments.",
            "total_matches": result.total_matches,
            "scheduled_matches": result.total_matches,  # Same as total_matches for Saturday schedule
            "schedule_id": str(result.schedule_id),
            "schedule_date": result.week_start_date.strftime("%Y-%m-%d"),
            "court_utilization_score": result.court_utilization_score,
            "team_preference_score": result.team_preference_score,
            "fairness_score": result.fairness_score
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating schedule: {str(e)}")

@app.post("/scheduler/optimize")
async def optimize_schedule(
    schedule_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Optimize an existing schedule"""
    try:
        scheduler = SportifyScheduler(db)
        result = scheduler.optimize_schedule(schedule_id)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "improvements": result.get("improvements", [])
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing schedule: {str(e)}")

# Export endpoints
@app.post("/export/schedule", response_model=ExportResponse)
async def export_schedule(
    export_request: ExportRequest,
    db: Session = Depends(get_db)
):
    """Export schedule in various formats"""
    try:
        # Get matches for the specified date
        matches = db.query(Match).filter(Match.scheduled_date == export_request.date).all()
        
        if not matches:
            raise HTTPException(status_code=404, detail="No matches found for the specified date")
        
        # Format data based on export type
        if export_request.format == "json":
            export_data = {
                "date": export_request.date.strftime("%Y-%m-%d"),
                "matches": [
                    {
                        "id": str(match.id),
                        "team1": match.team1.name if match.team1 else "Unknown",
                        "team2": match.team2.name if match.team2 else "Unknown",
                        "court": match.court.name if match.court else "Unknown",
                        "time": match.time_slot.start_time.strftime("%H:%M") if match.time_slot else "Unknown",
                        "tournament": match.team1.tournament.name if match.team1 and match.team1.tournament else "Unknown"
                    }
                    for match in matches
                ]
            }
        elif export_request.format == "csv":
            csv_data = "Date,Team1,Team2,Court,Time,Tournament\n"
            for match in matches:
                csv_data += f"{export_request.date.strftime('%Y-%m-%d')},{match.team1.name if match.team1 else 'Unknown'},{match.team2.name if match.team2 else 'Unknown'},{match.court.name if match.court else 'Unknown'},{match.time_slot.start_time.strftime('%H:%M') if match.time_slot else 'Unknown'},{match.team1.tournament.name if match.team1 and match.team1.tournament else 'Unknown'}\n"
            export_data = csv_data
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
        
        return ExportResponse(
            success=True,
            format=export_request.format,
            data=export_data,
            filename=f"schedule_{export_request.date.strftime('%Y%m%d')}.{export_request.format}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting schedule: {str(e)}")

# Team restriction endpoints
@app.get("/team-restrictions", response_model=TeamRestrictionListResponse)
async def get_team_restrictions(
    team_id: Optional[uuid.UUID] = None,
    restriction_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get team restrictions"""
    query = db.query(TeamRestriction)
    if team_id:
        query = query.filter(TeamRestriction.team_id == team_id)
    if restriction_date:
        query = query.filter(TeamRestriction.restriction_date == restriction_date)
    
    restrictions = query.offset(skip).limit(limit).all()
    return TeamRestrictionListResponse(
        restrictions=[TeamRestrictionResponse.from_orm(r) for r in restrictions],
        total=len(restrictions),
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@app.post("/team-restrictions", response_model=TeamRestrictionResponse)
async def create_team_restriction(
    restriction: TeamRestrictionCreate,
    db: Session = Depends(get_db)
):
    """Create or update a team restriction"""
    # Check if restriction already exists
    existing = db.query(TeamRestriction).filter(
        TeamRestriction.team_id == restriction.team_id,
        TeamRestriction.restriction_date == restriction.restriction_date,
        TeamRestriction.restriction_type == restriction.restriction_type
    ).first()
    
    if existing:
        # Update existing restriction
        for field, value in restriction.dict(exclude_unset=True).items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return TeamRestrictionResponse.from_orm(existing)
    else:
        # Create new restriction
        db_restriction = TeamRestriction(**restriction.dict())
        db.add(db_restriction)
        db.commit()
        db.refresh(db_restriction)
        return TeamRestrictionResponse.from_orm(db_restriction)

@app.put("/team-restrictions/{restriction_id}", response_model=TeamRestrictionResponse)
async def update_team_restriction(
    restriction_id: uuid.UUID,
    restriction: TeamRestrictionUpdate,
    db: Session = Depends(get_db)
):
    """Update a team restriction"""
    db_restriction = db.query(TeamRestriction).filter(TeamRestriction.id == restriction_id).first()
    if not db_restriction:
        raise HTTPException(status_code=404, detail="Team restriction not found")
    
    for field, value in restriction.dict(exclude_unset=True).items():
        setattr(db_restriction, field, value)
    
    db.commit()
    db.refresh(db_restriction)
    return TeamRestrictionResponse.from_orm(db_restriction)

@app.delete("/team-restrictions/{restriction_id}")
async def delete_team_restriction(restriction_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a team restriction"""
    restriction = db.query(TeamRestriction).filter(TeamRestriction.id == restriction_id).first()
    if not restriction:
        raise HTTPException(status_code=404, detail="Team restriction not found")
    
    db.delete(restriction)
    db.commit()
    return {"message": "Team restriction deleted successfully"}

# Tournament fixture endpoints
@app.get("/tournaments/{tournament_id}/fixtures", response_model=TournamentFixtureListResponse)
async def get_tournament_fixtures(
    tournament_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get all fixtures for a tournament"""
    fixtures = db.query(TournamentFixture).join(
        TournamentRound, TournamentFixture.tournament_round_id == TournamentRound.id
    ).filter(
        TournamentRound.tournament_id == tournament_id
    ).all()
    
    return TournamentFixtureListResponse(
        fixtures=[TournamentFixtureResponse.from_orm(f) for f in fixtures],
        total=len(fixtures),
        page=1,
        size=len(fixtures)
    )

@app.post("/tournaments/{tournament_id}/generate-fixtures")
async def generate_tournament_fixtures(
    tournament_id: uuid.UUID,
    preserve_scores: bool = False,
    db: Session = Depends(get_db)
):
    """Generate tournament fixtures"""
    try:
        tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            raise HTTPException(status_code=404, detail="Tournament not found")
        
        generator = TournamentFixtureGenerator(db)
        result = generator.generate_tournament_structure(tournament_id, preserve_scores)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "fixtures_created": result["fixtures_created"],
                "rounds_created": result["rounds_created"],
                "groups_created": result["groups_created"]
            }
        else:
            if result.get("warning") == "existing_scores":
                return {
                    "success": False,
                    "warning": "existing_scores",
                    "message": result["message"]
                }
            else:
                raise HTTPException(status_code=400, detail=result["message"])
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating fixtures: {str(e)}")

@app.put("/fixtures/{fixture_id}/result")
async def update_fixture_result(
    fixture_id: uuid.UUID,
    team1_score: int,
    team2_score: int,
    updated_by: str = Query(..., description="Who is updating the result"),
    db: Session = Depends(get_db)
):
    """Update fixture result"""
    try:
        fixture = db.query(TournamentFixture).filter(TournamentFixture.id == fixture_id).first()
        if not fixture:
            raise HTTPException(status_code=404, detail="Fixture not found")
        
        # Log warning if overwriting existing scores
        if fixture.team1_score != 0 or fixture.team2_score != 0:
            print(f"WARNING: Overwriting existing scores for fixture {fixture_id}: {fixture.team1_score}-{fixture.team2_score} -> {team1_score}-{team2_score}")
        
        # Update fixture
        fixture.team1_score = team1_score
        fixture.team2_score = team2_score
        fixture.status = "completed"
        fixture.last_updated_by = updated_by
        fixture.last_updated_at = datetime.utcnow()
        
        db.commit()
        
        # Update standings if this is a group match
        if fixture.tournament_group_id:
            _update_group_standings(db, fixture)
        
        return {
            "success": True,
            "message": "Fixture result updated successfully",
            "fixture_id": str(fixture_id),
            "team1_score": team1_score,
            "team2_score": team2_score,
            "updated_by": updated_by
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating fixture result: {str(e)}")

def _update_group_standings(db: Session, fixture: TournamentFixture):
    """Update group standings after a fixture result"""
    if not fixture.tournament_group_id:
        return
    
    # Get all teams in the group
    group_teams = db.query(Team).filter(Team.tournament_group_id == fixture.tournament_group_id).all()
    
    # Clear existing standings
    db.query(TournamentStanding).filter(
        TournamentStanding.tournament_group_id == fixture.tournament_group_id
    ).delete()
    
    # Calculate standings for each team
    team_stats = {}
    for team in group_teams:
        team_stats[team.id] = {
            "team": team,
            "wins": 0,
            "losses": 0,
            "points_for": 0,
            "points_against": 0,
            "points": 0
        }
    
    # Get all completed fixtures in the group
    completed_fixtures = db.query(TournamentFixture).filter(
        TournamentFixture.tournament_group_id == fixture.tournament_group_id,
        TournamentFixture.status == "completed"
    ).all()
    
    # Calculate stats
    for fixture in completed_fixtures:
        team1_id = fixture.team1_id
        team2_id = fixture.team2_id
        team1_score = fixture.team1_score
        team2_score = fixture.team2_score
        
        if team1_id in team_stats and team2_id in team_stats:
            # Update points for/against
            team_stats[team1_id]["points_for"] += team1_score
            team_stats[team1_id]["points_against"] += team2_score
            team_stats[team2_id]["points_for"] += team2_score
            team_stats[team2_id]["points_against"] += team1_score
            
            # Update wins/losses and points
            if team1_score > team2_score:
                team_stats[team1_id]["wins"] += 1
                team_stats[team1_id]["points"] += 2  # 2 points for win
                team_stats[team2_id]["losses"] += 1
                team_stats[team2_id]["points"] += 1  # 1 point for loss
            elif team2_score > team1_score:
                team_stats[team2_id]["wins"] += 1
                team_stats[team2_id]["points"] += 2  # 2 points for win
                team_stats[team1_id]["losses"] += 1
                team_stats[team1_id]["points"] += 1  # 1 point for loss
    
    # Create standings
    group_standings = []
    for team_id, stats in team_stats.items():
        standing = TournamentStanding(
            tournament_group_id=fixture.tournament_group_id,
            team_id=team_id,
            wins=stats["wins"],
            losses=stats["losses"],
            points_for=stats["points_for"],
            points_against=stats["points_against"],
            points_difference=stats["points_for"] - stats["points_against"],
            points=stats["points"]
        )
        group_standings.append(standing)
        db.add(standing)
    
    db.commit()
    
    # Sort by tournament points (desc), then points difference (desc)
    group_standings.sort(key=lambda x: (x.points, x.points_difference), reverse=True)
    
    for i, standing in enumerate(group_standings):
        standing.position = i + 1

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)