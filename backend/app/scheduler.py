from ortools.sat.python import cp_model
from typing import List, Dict, Tuple, Optional
from datetime import date, timedelta
import time
from sqlalchemy.orm import Session
from app.models import Tournament, Team, Court, TimeSlot, Match, Schedule, ScheduleMatch, TeamRestriction, TournamentFixture
from app.schemas import SchedulerRequest, SchedulerResponse
import uuid

class SportifyScheduler:
    """OR-Tools based scheduler for sports tournaments"""
    
    def __init__(self, db: Session):
        self.db = db
        self.model = None
        self.solver = None
        
    def create_schedule(self, request: SchedulerRequest) -> SchedulerResponse:
        """Create a new schedule using OR-Tools CP-SAT"""
        start_time = time.time()
        
        try:
            # Fetch data from database
            tournament = self.db.query(Tournament).filter(Tournament.id == request.tournament_id).first()
            if not tournament:
                raise ValueError("Tournament not found")
                
            teams = self.db.query(Team).filter(
                Team.tournament_id == request.tournament_id,
                Team.is_active == True
            ).all()
            
            courts = self.db.query(Court).filter(Court.is_active == True).all()
            time_slots = self.db.query(TimeSlot).filter(TimeSlot.is_active == True).all()
            
            if not teams or not courts or not time_slots:
                raise ValueError("Insufficient data for scheduling")
            
            # Create the optimization model
            self.model = cp_model.CpModel()
            
            # Create variables
            match_vars = self._create_match_variables(teams, courts, time_slots)
            
            # Add constraints
            self._add_basic_constraints(match_vars, teams, courts, time_slots)
            self._add_team_constraints(match_vars, teams, request.max_matches_per_team_per_week)
            self._add_court_constraints(match_vars, courts, time_slots)
            self._add_time_constraints(match_vars, teams, time_slots)
            self._add_tournament_constraints(match_vars, teams)
            
            # Add objective function
            objective = self._create_objective_function(
                match_vars, teams, courts, time_slots,
                request.fairness_weight,
                request.court_utilization_weight,
                request.team_preference_weight
            )
            
            self.model.Maximize(objective)
            
            # Solve the model
            self.solver = cp_model.CpSolver()
            self.solver.parameters.max_time_in_seconds = 300.0  # 5 minutes max
            self.solver.parameters.num_search_workers = 8
            
            status = self.solver.Solve(self.model)
            
            if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                # Extract solution and save to database
                schedule_id = self._save_schedule(request, tournament)
                matches_created = self._save_matches(match_vars, teams, courts, time_slots, schedule_id)
                
                # Calculate metrics
                fairness_score = self._calculate_fairness_score(matches_created, teams)
                court_utilization_score = self._calculate_court_utilization_score(matches_created, courts, time_slots)
                team_preference_score = self._calculate_team_preference_score(matches_created, teams, time_slots)
                
                processing_time = time.time() - start_time
                
                return SchedulerResponse(
                    schedule_id=schedule_id,
                    tournament_id=request.tournament_id,
                    week_start_date=request.week_start_date,
                    week_end_date=request.week_end_date,
                    total_matches=len(matches_created),
                    total_courts_used=len(set(m.court_id for m in matches_created if m.court_id)),
                    total_time_slots_used=len(set(m.time_slot_id for m in matches_created if m.time_slot_id)),
                    fairness_score=fairness_score,
                    court_utilization_score=court_utilization_score,
                    team_preference_score=team_preference_score,
                    processing_time_seconds=processing_time,
                    status="success",
                    message=f"Schedule created successfully with {len(matches_created)} matches"
                )
            else:
                raise ValueError(f"Solver failed with status: {status}")
                
        except Exception as e:
            processing_time = time.time() - start_time
            return SchedulerResponse(
                schedule_id=uuid.uuid4(),
                tournament_id=request.tournament_id,
                week_start_date=request.week_start_date,
                week_end_date=request.week_end_date,
                total_matches=0,
                total_courts_used=0,
                total_time_slots_used=0,
                fairness_score=0.0,
                court_utilization_score=0.0,
                team_preference_score=0.0,
                processing_time_seconds=processing_time,
                status="error",
                message=f"Scheduling failed: {str(e)}"
            )

    def create_saturday_schedule(self, request_date: date) -> SchedulerResponse:
        """Create a comprehensive Saturday schedule for all tournaments"""
        start_time = time.time()
        
        try:
            # Fetch all tournaments
            tournaments = self.db.query(Tournament).all()
            if not tournaments:
                raise ValueError("No tournaments found")
            
            # Fetch all teams from all tournaments
            all_teams = self.db.query(Team).filter(Team.is_active == True).all()
            if not all_teams:
                raise ValueError("No teams found")
            
            # Fetch all courts and time slots
            courts = self.db.query(Court).filter(Court.is_active == True).all()
            time_slots = self.db.query(TimeSlot).filter(TimeSlot.is_active == True).all()
            
            if not courts or not time_slots:
                raise ValueError("No courts or time slots available")
            
            # Clear existing matches for this Saturday date
            existing_matches = self.db.query(Match).filter(Match.scheduled_date == request_date).all()
            for match in existing_matches:
                # Reset fixture status back to pending
                fixture = self.db.query(TournamentFixture).filter(
                    TournamentFixture.match_id == match.id
                ).first()
                if fixture:
                    fixture.status = "pending"
                    fixture.match_id = None
                    self.db.add(fixture)
                
                # Delete associated schedule matches first
                self.db.query(ScheduleMatch).filter(ScheduleMatch.match_id == match.id).delete()
                # Delete the match
                self.db.delete(match)
            
            # Reset fixtures marked as "scheduled" back to "pending" 
            # BUT preserve fixtures that have scores (completed games)
            scheduled_fixtures = self.db.query(TournamentFixture).filter(
                TournamentFixture.status == "scheduled"
            ).all()
            for fixture in scheduled_fixtures:
                # Only reset if the fixture has no scores (0-0) or is truly orphaned
                if fixture.team1_score == 0 and fixture.team2_score == 0:
                    fixture.status = "pending"
                    fixture.match_id = None  # Clear the match_id as well
                    self.db.add(fixture)
                else:
                    # Fixture has scores, mark it as completed instead of pending
                    fixture.status = "completed"
                    self.db.add(fixture)
            
            self.db.commit()
            
            # Create the optimization model
            self.model = cp_model.CpModel()
            
            # Create variables for all possible matches across all tournaments
            match_vars = self._create_all_tournament_matches(all_teams, courts, time_slots)
            
            # Add constraints
            self._add_basic_constraints(match_vars, all_teams, courts, time_slots)
            self._add_tournament_boundary_constraints(match_vars, all_teams)
            self._add_court_constraints(match_vars, courts, time_slots)
            self._add_time_constraints(match_vars, all_teams, time_slots)
            self._add_saturday_team_constraints(match_vars, all_teams)
            self._add_team_restriction_constraints(match_vars, all_teams, courts, time_slots, request_date)
            # Disabled multi-tournament rest constraint due to exponential constraint explosion
            # self._add_multi_tournament_rest_constraints_optimized(match_vars, all_teams, time_slots)
            
            # Add objective function
            objective = self._create_comprehensive_objective(
                match_vars, all_teams, courts, time_slots
            )
            
            self.model.Maximize(objective)
            
            # Solve the model
            self.solver = cp_model.CpSolver()
            self.solver.parameters.max_time_in_seconds = 600.0  # Increased timeout to 10 minutes
            self.solver.parameters.num_search_workers = 8
            status = self.solver.Solve(self.model)
            
            if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                # Create one schedule for the Saturday
                schedule = Schedule(
                    tournament_id=None,  # This schedule covers all tournaments
                    week_start_date=request_date,
                    week_end_date=request_date,
                    status="draft"
                )
                self.db.add(schedule)
                self.db.commit()
                self.db.refresh(schedule)
                
                # Save all matches
                matches_created = self._save_all_tournament_matches(
                    match_vars, all_teams, courts, time_slots, schedule.id, request_date
                )
                
                # Calculate metrics
                fairness_score = self._calculate_fairness_score(matches_created, all_teams)
                court_utilization_score = self._calculate_court_utilization_score(matches_created, courts, time_slots)
                team_preference_score = self._calculate_team_preference_score(matches_created, all_teams, time_slots)
                
                processing_time = time.time() - start_time
                
                return SchedulerResponse(
                    schedule_id=schedule.id,
                    tournament_id=None,
                    week_start_date=request_date,
                    week_end_date=request_date,
                    total_matches=len(matches_created),
                    total_courts_used=len(set(m.court_id for m in matches_created if m.court_id)),
                    total_time_slots_used=len(set(m.time_slot_id for m in matches_created if m.time_slot_id)),
                    fairness_score=fairness_score,
                    court_utilization_score=court_utilization_score,
                    team_preference_score=team_preference_score,
                    processing_time_seconds=processing_time,
                    status="success",
                    message=f"Saturday schedule created successfully with {len(matches_created)} matches across all tournaments"
                )
            else:
                raise ValueError(f"Solver failed with status: {status}")
                
        except Exception as e:
            processing_time = time.time() - start_time
            return SchedulerResponse(
                schedule_id=uuid.uuid4(),
                tournament_id=None,
                week_start_date=request_date,
                week_end_date=request_date,
                total_matches=0,
                total_courts_used=0,
                total_time_slots_used=0,
                fairness_score=0.0,
                court_utilization_score=0.0,
                team_preference_score=0.0,
                processing_time_seconds=processing_time,
                status="error",
                message=f"Saturday scheduling failed: {str(e)}"
            )
    
    def create_sunday_schedule(self, request_date: date) -> SchedulerResponse:
        """Create a comprehensive Sunday schedule for all tournaments using OR-Tools CP-SAT"""
        start_time = time.time()
        
        try:
            # Fetch Sunday tournaments (Maxi 40 Masculino, Maxi 50 Masculino, Maxi 50 Femenino)
            sunday_tournaments = self.db.query(Tournament).filter(
                Tournament.name.in_([
                    'Maxi 40 Masculino',
                    'Maxi 50 Masculino', 
                    'Maxi 50 Femenino'
                ])
            ).all()
            
            if not sunday_tournaments:
                raise ValueError("No Sunday tournaments found")
            
            # Fetch all teams from Sunday tournaments
            all_teams = []
            for tournament in sunday_tournaments:
                tournament_teams = self.db.query(Team).filter(
                    Team.tournament_id == tournament.id,
                    Team.is_active == True
                ).all()
                all_teams.extend(tournament_teams)
            
            if not all_teams:
                raise ValueError("No teams found for Sunday tournaments")
            
            # Fetch courts
            courts = self.db.query(Court).filter(Court.is_active == True).all()
            if not courts:
                raise ValueError("No active courts found")
            
            # Fetch Sunday time slots (day_of_week = 0 for Sunday)
            time_slots = self.db.query(TimeSlot).filter(
                TimeSlot.day_of_week == 0,  # Sunday
                TimeSlot.is_active == True
            ).all()
            
            if not time_slots:
                raise ValueError("No Sunday time slots found")
            
            # Clear existing matches for this Sunday date
            existing_matches = self.db.query(Match).filter(Match.scheduled_date == request_date).all()
            for match in existing_matches:
                # Reset fixture status back to pending
                fixture = self.db.query(TournamentFixture).filter(
                    TournamentFixture.match_id == match.id
                ).first()
                if fixture:
                    fixture.status = "pending"
                    fixture.match_id = None
                    self.db.add(fixture)
                
                # Delete associated schedule matches first
                self.db.query(ScheduleMatch).filter(ScheduleMatch.match_id == match.id).delete()
                # Delete the match
                self.db.delete(match)
            
            # Reset fixtures marked as "scheduled" back to "pending" 
            # BUT preserve fixtures that have scores (completed games)
            scheduled_fixtures = self.db.query(TournamentFixture).filter(
                TournamentFixture.status == "scheduled"
            ).all()
            for fixture in scheduled_fixtures:
                # Only reset if the fixture has no scores (0-0) or is truly orphaned
                if fixture.team1_score == 0 and fixture.team2_score == 0:
                    fixture.status = "pending"
                    fixture.match_id = None  # Clear the match_id as well
                    self.db.add(fixture)
                else:
                    # Fixture has scores, mark it as completed instead of pending
                    fixture.status = "completed"
                    self.db.add(fixture)
            
            self.db.commit()
            
            # Create the optimization model
            self.model = cp_model.CpModel()
            
            # Create variables for all possible matches across all Sunday tournaments
            match_vars = self._create_sunday_tournament_matches(all_teams, courts, time_slots)
            
            # Add constraints
            self._add_basic_constraints(match_vars, all_teams, courts, time_slots)
            self._add_tournament_boundary_constraints(match_vars, all_teams)
            self._add_court_constraints(match_vars, courts, time_slots)
            self._add_time_constraints(match_vars, all_teams, time_slots)
            self._add_sunday_team_constraints(match_vars, all_teams)
            self._add_team_restriction_constraints(match_vars, all_teams, courts, time_slots, request_date)
            
            # Add objective function
            objective = self._create_comprehensive_objective(
                match_vars, all_teams, courts, time_slots
            )
            
            self.model.Maximize(objective)
            
            # Solve the model
            self.solver = cp_model.CpSolver()
            self.solver.parameters.max_time_in_seconds = 600.0  # 10 minutes max
            self.solver.parameters.num_search_workers = 8
            status = self.solver.Solve(self.model)
            
            if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                # Create one schedule for the Sunday
                schedule = Schedule(
                    tournament_id=None,  # This schedule covers all tournaments
                    week_start_date=request_date,
                    week_end_date=request_date,
                    status="draft"
                )
                self.db.add(schedule)
                self.db.commit()
                self.db.refresh(schedule)
                
                # Save all matches
                matches_created = self._save_sunday_tournament_matches(
                    match_vars, all_teams, courts, time_slots, schedule.id, request_date
                )
                
                # Calculate metrics
                fairness_score = self._calculate_fairness_score(matches_created, all_teams)
                court_utilization_score = self._calculate_court_utilization_score(matches_created, courts, time_slots)
                team_preference_score = self._calculate_team_preference_score(matches_created, all_teams, time_slots)
                
                processing_time = time.time() - start_time
                
                return SchedulerResponse(
                    schedule_id=schedule.id,
                    tournament_id=None,
                    week_start_date=request_date,
                    week_end_date=request_date,
                    total_matches=len(matches_created),
                    total_courts_used=len(set(m.court_id for m in matches_created if m.court_id)),
                    total_time_slots_used=len(set(m.time_slot_id for m in matches_created if m.time_slot_id)),
                    fairness_score=fairness_score,
                    court_utilization_score=court_utilization_score,
                    team_preference_score=team_preference_score,
                    processing_time_seconds=processing_time,
                    status="success",
                    message=f"Sunday schedule created successfully with {len(matches_created)} matches across all tournaments"
                )
            else:
                raise ValueError(f"Solver failed with status: {status}")
                
        except Exception as e:
            processing_time = time.time() - start_time
            return SchedulerResponse(
                schedule_id=uuid.uuid4(),
                tournament_id=None,
                week_start_date=request_date,
                week_end_date=request_date,
                total_matches=0,
                total_courts_used=0,
                total_time_slots_used=0,
                fairness_score=0.0,
                court_utilization_score=0.0,
                team_preference_score=0.0,
                processing_time_seconds=processing_time,
                status="error",
                message=f"Sunday scheduling failed: {str(e)}"
            )
    
    def _create_sunday_tournament_matches(self, all_teams, courts, time_slots):
        """Create match variables only for available fixtures from Sunday tournaments"""
        match_vars = {}
        
        # Get available fixtures from Sunday tournaments only
        sunday_tournament_ids = [t.tournament_id for t in all_teams]
        available_fixtures = self.db.query(TournamentFixture).filter(
            TournamentFixture.status == "pending",
            TournamentFixture.team1_id.in_([t.id for t in all_teams]),
            TournamentFixture.team2_id.in_([t.id for t in all_teams])
        ).all()
        
        # Create match variables only for available fixtures
        for fixture in available_fixtures:
            # Find the team objects
            team1 = next((t for t in all_teams if t.id == fixture.team1_id), None)
            team2 = next((t for t in all_teams if t.id == fixture.team2_id), None)
            
            if not team1 or not team2:
                continue  # Skip if team not found
                
            for court in courts:
                for time_slot in time_slots:
                    key = (team1.id, team2.id, court.id, time_slot.id)
                    match_vars[key] = self.model.NewBoolVar(f'sunday_match_{team1.id}_{team2.id}_{court.id}_{time_slot.id}')
        
        return match_vars
    
    def _create_sunday_shared_matches(self, tournaments, all_teams, courts, time_slots, schedule_id, request_date):
        """Create matches across all tournaments ensuring only 1 game per court per time slot"""
        matches_created = []
        
        print(f"Creating shared matches for {len(tournaments)} tournaments")
        print(f"Total teams: {len(all_teams)}, Courts: {len(courts)}, Time slots: {len(time_slots)}")
        
        # Group teams by tournament
        teams_by_tournament = {}
        for team in all_teams:
            if team.tournament_id not in teams_by_tournament:
                teams_by_tournament[team.tournament_id] = []
            teams_by_tournament[team.tournament_id].append(team)
        
        # Create team pairs for each tournament
        tournament_pairs = {}
        for tournament_id, teams in teams_by_tournament.items():
            pairs = []
            for i in range(len(teams)):
                for j in range(i + 1, len(teams)):
                    pairs.append((teams[i], teams[j]))
            tournament_pairs[tournament_id] = pairs
            print(f"Tournament {tournament_id}: {len(teams)} teams, {len(pairs)} pairs")
        
        # Create matches ensuring only 1 game per court per time slot AND only 1 game per team per day
        match_index = 0
        total_slots = len(courts) * len(time_slots)
        used_teams = set()  # Track teams that have already played today
        
        print(f"Total available slots: {total_slots}")
        
        for court in courts:
            for time_slot in time_slots:
                if match_index >= total_slots:
                    break
                
                # Find a tournament with available pairs where both teams haven't played today
                match_found = False
                for tournament_id, pairs in tournament_pairs.items():
                    # Find a pair where both teams haven't played today
                    for i, (team1, team2) in enumerate(pairs):
                        if team1.id not in used_teams and team2.id not in used_teams:
                            # Found a valid pair - both teams can play
                            pairs.pop(i)  # Remove this pair from available pairs
                            
                            print(f"Creating match: {team1.name} vs {team2.name} at {court.name} {time_slot.start_time}")
                            
                            # Create match
                            match = Match(
                                team1_id=team1.id,
                                team2_id=team2.id,
                                court_id=court.id,
                                time_slot_id=time_slot.id,
                                scheduled_date=request_date,
                                scheduled_time=time_slot.start_time,
                                status="scheduled",
                                score_team1=0,
                                score_team2=0,
                                tournament_id=tournament_id
                            )
                            
                            self.db.add(match)
                            matches_created.append(match)
                            match_index += 1
                            match_found = True
                            
                            # Mark both teams as used for today
                            used_teams.add(team1.id)
                            used_teams.add(team2.id)
                            break
                    
                    if match_found:
                        break
                
                if not match_found:
                    break  # No more valid matches available
        
        try:
            self.db.commit()
            print(f"Successfully committed {len(matches_created)} matches to database")
            
            # Create entries in schedule_matches table
            for match in matches_created:
                schedule_match = ScheduleMatch(
                    schedule_id=schedule_id,
                    match_id=match.id
                )
                self.db.add(schedule_match)
            
            self.db.commit()
            print(f"Successfully linked {len(matches_created)} matches to schedule")
        except Exception as e:
            print(f"Error committing matches: {e}")
            self.db.rollback()
        
        return matches_created
    
    def _create_match_variables(self, teams: List[Team], courts: List[Court], time_slots: List[TimeSlot]):
        """Create binary variables for each possible match assignment based on fixtures"""
        match_vars = {}
        
        # Get available fixtures for this tournament
        tournament_id = teams[0].tournament_id if teams else None
        if not tournament_id:
            return match_vars
            
        available_fixtures = self.db.query(TournamentFixture).join(
            TournamentFixture.round
        ).filter(
            TournamentFixture.status == "pending",
            TournamentFixture.round.has(tournament_id=tournament_id)
        ).all()
        
        # Create match variables only for available fixtures
        for fixture in available_fixtures:
            # Find the team objects
            team1 = next((t for t in teams if t.id == fixture.team1_id), None)
            team2 = next((t for t in teams if t.id == fixture.team2_id), None)
            
            if not team1 or not team2:
                continue  # Skip if team not found
                
            for court in courts:
                for time_slot in time_slots:
                    key = (team1.id, team2.id, court.id, time_slot.id)
                    match_vars[key] = self.model.NewBoolVar(f'match_{team1.id}_{team2.id}_{court.id}_{time_slot.id}')
        
        return match_vars

    def _get_available_fixtures(self, all_teams):
        """Get all pending fixtures that can be scheduled"""
        # Get all pending fixtures from all tournaments
        pending_fixtures = self.db.query(TournamentFixture).filter(
            TournamentFixture.status == "pending"
        ).all()
        
        # Filter fixtures for active teams only
        active_team_ids = {team.id for team in all_teams}
        available_fixtures = []
        
        for fixture in pending_fixtures:
            # Check if both teams are active
            if fixture.team1_id in active_team_ids and fixture.team2_id in active_team_ids:
                available_fixtures.append(fixture)
        return available_fixtures

    def _create_all_tournament_matches(self, all_teams, courts, time_slots):
        """Create match variables only for available fixtures"""
        match_vars = {}
        
        # Get available fixtures instead of creating all possible matches
        available_fixtures = self._get_available_fixtures(all_teams)
        
        # Create match variables only for available fixtures
        for fixture in available_fixtures:
            # Find the team objects
            team1 = next((t for t in all_teams if t.id == fixture.team1_id), None)
            team2 = next((t for t in all_teams if t.id == fixture.team2_id), None)
            
            if not team1 or not team2:
                continue  # Skip if team not found
                
            for court in courts:
                for time_slot in time_slots:
                    key = (team1.id, team2.id, court.id, time_slot.id)
                    match_vars[key] = self.model.NewBoolVar(f'match_{team1.id}_{team2.id}_{court.id}_{time_slot.id}')
        
        return match_vars
    
    def _add_basic_constraints(self, match_vars, teams, courts, time_slots):
        """Add basic scheduling constraints"""
        # Each team can only play one match at a time
        for team in teams:
            for time_slot in time_slots:
                constraint = []
                for (team1_id, team2_id, court_id, ts_id), var in match_vars.items():
                    if ts_id == time_slot.id and (team1_id == team.id or team2_id == team.id):
                        constraint.append(var)
                if constraint:
                    self.model.Add(sum(constraint) <= 1)
        
        # Each court can only host one match at a time
        for court in courts:
            for time_slot in time_slots:
                constraint = []
                for (team1_id, team2_id, court_id, ts_id), var in match_vars.items():
                    if court_id == court.id and ts_id == time_slot.id:
                        constraint.append(var)
                if constraint:
                    self.model.Add(sum(constraint) <= 1)
    
    def _add_team_constraints(self, match_vars, teams, max_matches_per_week):
        """Add constraints for team match limits"""
        for team in teams:
            constraint = []
            for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
                if team1_id == team.id or team2_id == team.id:
                    constraint.append(var)
            if constraint:
                self.model.Add(sum(constraint) <= max_matches_per_week)
    
    def _add_court_constraints(self, match_vars, courts, time_slots):
        """Add constraints for court availability"""
        # Ensure each court is used efficiently
        for court in courts:
            court_matches = []
            for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
                if court_id == court.id:
                    court_matches.append(var)
            if court_matches:
                # Encourage court usage but don't force it
                pass
    
    def _add_time_constraints(self, match_vars, teams, time_slots):
        """Add constraints for team time preferences"""
        for team in teams:
            for time_slot in time_slots:
                # Check if time slot is within team's preferred window
                if (time_slot.day_of_week not in team.preferred_days or
                    time_slot.start_time < team.earliest_start_time or
                    time_slot.end_time > team.latest_start_time):
                    
                    # Penalize assignments outside preferred times
                    for (team1_id, team2_id, court_id, ts_id), var in match_vars.items():
                        if ts_id == time_slot.id and (team1_id == team.id or team2_id == team.id):
                            # Add penalty to objective function (handled in objective)
                            pass

    def _add_tournament_constraints(self, match_vars, teams):
        """Add constraints to ensure teams only play within their own tournament"""
        # Group teams by tournament
        teams_by_tournament = {}
        for team in teams:
            if team.tournament_id not in teams_by_tournament:
                teams_by_tournament[team.tournament_id] = []
            teams_by_tournament[team.tournament_id].append(team)
        
        # Add constraint: teams can only play against teams in the same tournament
        for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
            team1 = next(t for t in teams if t.id == team1_id)
            team2 = next(t for t in teams if t.id == team2_id)
            
            # If teams are from different tournaments, force this match to be 0
            if team1.tournament_id != team2.tournament_id:
                self.model.Add(var == 0)

    def _add_tournament_boundary_constraints(self, match_vars, all_teams):
        """Ensure teams only play within their own tournament"""
        # Group teams by tournament
        teams_by_tournament = {}
        for team in all_teams:
            if team.tournament_id not in teams_by_tournament:
                teams_by_tournament[team.tournament_id] = []
            teams_by_tournament[team.tournament_id].append(team)
        
        # Add constraint: teams can only play against teams in the same tournament
        for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
            team1 = next(t for t in all_teams if t.id == team1_id)
            team2 = next(t for t in all_teams if t.id == team2_id)
            
            # If teams are from different tournaments, force this match to be 0
            if team1.tournament_id != team2.tournament_id:
                self.model.Add(var == 0)

    def _add_saturday_team_constraints(self, match_vars, all_teams):
        """Add constraints to ensure each team plays at most once per day per tournament (Saturday)"""
        for team in all_teams:
            team_matches = []
            for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
                if team1_id == team.id or team2_id == team.id:
                    team_matches.append(var)
            
            # Each team can play at most 1 match per day per tournament
            # This ensures fair play - no team plays twice in the same tournament on the same day
            # Teams in different tournaments can play separately
            if team_matches:
                self.model.Add(sum(team_matches) <= 1)  # At most once per tournament per day
    
    def _add_sunday_team_constraints(self, match_vars, all_teams):
        """Add constraints to ensure each team plays at most once per day per tournament (Sunday)"""
        for team in all_teams:
            team_matches = []
            for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
                if team1_id == team.id or team2_id == team.id:
                    team_matches.append(var)
            
            # Each team can play at most 1 match per day per tournament
            # This ensures fair play - no team plays twice in the same tournament on the same day
            # Teams in different tournaments can play separately
            if team_matches:
                self.model.Add(sum(team_matches) <= 1)  # At most once per tournament per day
    
    def _create_objective_function(self, match_vars, teams, courts, time_slots, 
                                 fairness_weight, court_utilization_weight, team_preference_weight):
        """Create the objective function to maximize"""
        objective_terms = []
        
        # Base objective: maximize number of matches
        for var in match_vars.values():
            objective_terms.append(var * 1000)  # High weight for basic feasibility
        
        # Fairness: minimize variance in team match counts
        team_match_counts = []
        for team in teams:
            team_matches = []
            for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
                if team1_id == team.id or team2_id == team.id:
                    team_matches.append(var)
            if team_matches:
                team_match_counts.append(sum(team_matches))
        
        # Court utilization: encourage even distribution
        court_match_counts = []
        for court in courts:
            court_matches = []
            for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
                if court_id == court.id:
                    court_matches.append(var)
            if court_matches:
                court_match_counts.append(sum(court_matches))
        
        # Team preference: reward matches in preferred time slots
        preference_reward = 0
        for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
            team1 = next(t for t in teams if t.id == team1_id)
            team2 = next(t for t in teams if t.id == team2_id)
            time_slot = next(ts for ts in time_slots if ts.id == time_slot_id)
            
            # Check if both teams prefer this time slot
            if (time_slot.day_of_week in team1.preferred_days and
                time_slot.day_of_week in team2.preferred_days and
                time_slot.start_time >= team1.earliest_start_time and
                time_slot.end_time <= team1.latest_start_time and
                time_slot.start_time >= team2.earliest_start_time and
                time_slot.end_time <= team2.latest_start_time):
                preference_reward += var * 100
        
        objective_terms.append(preference_reward * team_preference_weight)
        
        return sum(objective_terms)

    def _create_comprehensive_objective(self, match_vars, all_teams, courts, time_slots):
        """Create objective function for comprehensive Saturday scheduling"""
        objective_terms = []
        
        # Base objective: maximize number of matches
        for var in match_vars.values():
            objective_terms.append(var * 1000)  # High weight for basic feasibility
        
        # Team preference: reward matches in preferred time slots
        preference_reward = 0
        for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
            team1 = next(t for t in all_teams if t.id == team1_id)
            team2 = next(t for t in all_teams if t.id == team2_id)
            time_slot = next(ts for ts in time_slots if ts.id == time_slot_id)
            
            # Check if both teams prefer this time slot
            if (time_slot.day_of_week in team1.preferred_days and
                time_slot.day_of_week in team2.preferred_days and
                time_slot.start_time >= team1.earliest_start_time and
                time_slot.end_time <= team1.latest_start_time and
                time_slot.start_time >= team2.earliest_start_time and
                time_slot.end_time <= team2.latest_start_time):
                preference_reward += var * 100
        
        objective_terms.append(preference_reward)
        
        return sum(objective_terms)
    
    def _save_schedule(self, request: SchedulerRequest, tournament: Tournament) -> uuid.UUID:
        """Save the schedule to the database"""
        schedule = Schedule(
            tournament_id=request.tournament_id,
            week_start_date=request.week_start_date,
            week_end_date=request.week_end_date,
            status="draft"
        )
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        return schedule.id
    
    def _save_matches(self, match_vars, teams, courts, time_slots, schedule_id: uuid.UUID) -> List[Match]:
        """Save the scheduled matches to the database and update fixture status"""
        matches = []
        
        for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
            if self.solver.Value(var) == 1:  # Match is scheduled
                time_slot = next(ts for ts in time_slots if ts.id == time_slot_id)
                court = next(c for c in courts if c.id == court_id)
                
                # Calculate actual date and time
                week_start = date.today()  # This should come from the request
                scheduled_date = week_start + timedelta(days=time_slot.day_of_week)
                
                match = Match(
                    tournament_id=teams[0].tournament_id,  # All teams have same tournament_id
                    team1_id=team1_id,
                    team2_id=team2_id,
                    court_id=court_id,
                    time_slot_id=time_slot_id,
                    scheduled_date=scheduled_date,
                    scheduled_time=time_slot.start_time,
                    status="scheduled"
                )
                
                self.db.add(match)
                matches.append(match)
        
        self.db.commit()
        
        # Refresh matches to get their IDs
        for match in matches:
            self.db.refresh(match)
        
        # Update fixture status to "scheduled" and link to match
        for match in matches:
            # Find the corresponding fixture
            fixture = self.db.query(TournamentFixture).filter(
                TournamentFixture.team1_id == match.team1_id,
                TournamentFixture.team2_id == match.team2_id,
                TournamentFixture.status == "pending"
            ).first()
            
            if fixture:
                fixture.status = "scheduled"
                fixture.match_id = match.id
                self.db.add(fixture)
        
        # Create schedule-match relationships
        for match in matches:
            schedule_match = ScheduleMatch(
                schedule_id=schedule_id,
                match_id=match.id
            )
            self.db.add(schedule_match)
        
        self.db.commit()
        return matches

    def _save_all_tournament_matches(self, match_vars, all_teams, courts, time_slots, schedule_id: uuid.UUID, request_date: date) -> List[Match]:
        """Save all scheduled matches to the database and update fixture status"""
        matches = []
        
        for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
            if self.solver.Value(var) == 1:  # Match is scheduled
                time_slot = next(ts for ts in time_slots if ts.id == time_slot_id)
                team1 = next(t for t in all_teams if t.id == team1_id)

                # Save matches exactly on the requested date (intended Saturday)
                scheduled_date = request_date

                match = Match(
                    tournament_id=team1.tournament_id,
                    team1_id=team1_id,
                    team2_id=team2_id,
                    court_id=court_id,
                    time_slot_id=time_slot_id,
                    scheduled_date=scheduled_date,
                    scheduled_time=time_slot.start_time,
                    status="scheduled"
                )
                
                self.db.add(match)
                matches.append(match)
        
        # Commit matches first to get their IDs
        self.db.commit()
        
        # Refresh matches to get their IDs
        for match in matches:
            self.db.refresh(match)
        
        # Update fixture status to "scheduled" and link to match
        for match in matches:
            # Find the corresponding fixture
            fixture = self.db.query(TournamentFixture).filter(
                TournamentFixture.team1_id == match.team1_id,
                TournamentFixture.team2_id == match.team2_id,
                TournamentFixture.status == "pending"
            ).first()
            
            if fixture:
                fixture.status = "scheduled"
                fixture.match_id = match.id
                self.db.add(fixture)
        
        # Create schedule-match relationships
        for match in matches:
            schedule_match = ScheduleMatch(
                schedule_id=schedule_id,
                match_id=match.id
            )
            self.db.add(schedule_match)
        
        self.db.commit()
        return matches
    
    def _save_sunday_tournament_matches(self, match_vars, all_teams, courts, time_slots, schedule_id: uuid.UUID, request_date: date) -> List[Match]:
        """Save all scheduled Sunday matches to the database and update fixture status"""
        matches = []
        
        for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
            if self.solver.Value(var) == 1:  # Match is scheduled
                time_slot = next(ts for ts in time_slots if ts.id == time_slot_id)
                team1 = next(t for t in all_teams if t.id == team1_id)

                # Save matches exactly on the requested date (intended Sunday)
                scheduled_date = request_date

                match = Match(
                    tournament_id=team1.tournament_id,
                    team1_id=team1_id,
                    team2_id=team2_id,
                    court_id=court_id,
                    time_slot_id=time_slot_id,
                    scheduled_date=scheduled_date,
                    scheduled_time=time_slot.start_time,
                    status="scheduled"
                )
                
                self.db.add(match)
                matches.append(match)
        
        # Commit matches first to get their IDs
        self.db.commit()
        
        # Refresh matches to get their IDs
        for match in matches:
            self.db.refresh(match)
        
        # Update fixture status to "scheduled" and link to match
        for match in matches:
            # Find the corresponding fixture
            fixture = self.db.query(TournamentFixture).filter(
                TournamentFixture.team1_id == match.team1_id,
                TournamentFixture.team2_id == match.team2_id,
                TournamentFixture.status == "pending"
            ).first()
            
            if fixture:
                fixture.status = "scheduled"
                fixture.match_id = match.id
                self.db.add(fixture)
        
        # Create schedule-match relationships
        for match in matches:
            schedule_match = ScheduleMatch(
                schedule_id=schedule_id,
                match_id=match.id
            )
            self.db.add(schedule_match)
        
        self.db.commit()
        return matches
    
    def _calculate_fairness_score(self, matches: List[Match], teams: List[Team]) -> float:
        """Calculate fairness score based on match distribution"""
        if not matches:
            return 0.0
        
        team_match_counts = {}
        for team in teams:
            team_match_counts[team.id] = 0
        
        for match in matches:
            team_match_counts[match.team1_id] += 1
            team_match_counts[match.team2_id] += 1
        
        # Calculate variance
        values = list(team_match_counts.values())
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        
        # Lower variance = higher fairness
        max_possible_variance = (max(values) - min(values)) ** 2 if values else 1
        fairness_score = 1.0 - (variance / max_possible_variance) if max_possible_variance > 0 else 1.0
        
        return max(0.0, min(1.0, fairness_score))
    
    def _calculate_court_utilization_score(self, matches: List[Match], courts: List[Court], time_slots: List[TimeSlot]) -> float:
        """Calculate court utilization score"""
        if not matches or not courts or not time_slots:
            return 0.0
        
        total_possible_slots = len(courts) * len(time_slots)
        used_slots = len(matches)
        
        utilization = used_slots / total_possible_slots if total_possible_slots > 0 else 0.0
        return min(1.0, utilization)
    
    def _calculate_team_preference_score(self, matches: List[Match], teams: List[Team], time_slots: List[TimeSlot]) -> float:
        """Calculate team preference satisfaction score"""
        if not matches:
            return 0.0
        
        preference_satisfied = 0
        total_matches = len(matches)
        
        for match in matches:
            team1 = next(t for t in teams if t.id == match.team1_id)
            team2 = next(t for t in teams if t.id == match.team2_id)
            time_slot = next(ts for ts in time_slots if ts.id == match.time_slot_id)
            
            # Check if both teams prefer this time slot
            if (time_slot.day_of_week in team1.preferred_days and
                time_slot.day_of_week in team2.preferred_days and
                time_slot.start_time >= team1.earliest_start_time and
                time_slot.end_time <= team1.latest_start_time and
                time_slot.start_time >= team2.earliest_start_time and
                time_slot.end_time <= team2.latest_start_time):
                preference_satisfied += 1
        
        return preference_satisfied / total_matches if total_matches > 0 else 0.0
    
    def _add_team_restriction_constraints(self, match_vars: Dict, teams: List[Team], 
                                        courts: List[Court], time_slots: List[TimeSlot], 
                                        request_date: date):
        """Add constraints based on team restrictions for the specific date"""
        import json
        
        # Get all team restrictions for the request date
        restrictions = self.db.query(TeamRestriction).filter(
            TeamRestriction.restriction_date == request_date
        ).all()
        
        # Create a mapping of team_id to restrictions
        team_restrictions = {}
        for restriction in restrictions:
            if restriction.team_id not in team_restrictions:
                team_restrictions[restriction.team_id] = []
            team_restrictions[restriction.team_id].append(restriction)
        
        # Apply restrictions for each team
        for team in teams:
            if team.id not in team_restrictions:
                continue
                
            team_restriction_list = team_restrictions[team.id]
            
            for restriction in team_restriction_list:
                if restriction.restriction_type == "not_scheduled":
                    # Team should not be scheduled at all
                    for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
                        if team1_id == team.id or team2_id == team.id:
                            self.model.Add(var == 0)
                
                elif restriction.restriction_type == "time_preference":
                    # Team has time preferences - ALL time preferences are hard constraints
                    if restriction.restriction_value:
                        try:
                            restriction_data = json.loads(restriction.restriction_value)
                            
                            # Handle earliest_time constraint (hard constraint)
                            if "earliest_time" in restriction_data:
                                earliest_time_str = restriction_data["earliest_time"]
                                # Convert time string to time object for comparison
                                from datetime import time as dt_time
                                earliest_time = dt_time.fromisoformat(earliest_time_str)
                                
                                # Find time slots that start before the earliest time
                                early_time_slots = [ts for ts in time_slots if ts.start_time < earliest_time]
                                
                                # Prevent scheduling in early time slots
                                for early_ts in early_time_slots:
                                    for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
                                        if (team1_id == team.id or team2_id == team.id) and time_slot_id == early_ts.id:
                                            self.model.Add(var == 0)
                            
                            # Handle preferred_times as HARD constraints (only allow preferred times)
                            if "preferred_times" in restriction_data:
                                preferred_times = restriction_data["preferred_times"]
                                if isinstance(preferred_times, list) and preferred_times:
                                    from datetime import time as dt_time
                                    # Convert preferred times to time objects
                                    preferred_time_objects = []
                                    for time_str in preferred_times:
                                        try:
                                            preferred_time_objects.append(dt_time.fromisoformat(time_str))
                                        except ValueError:
                                            continue
                                    
                                    if preferred_time_objects:
                                        # Find time slots that are NOT in the preferred times
                                        non_preferred_time_slots = [ts for ts in time_slots 
                                                                   if ts.start_time not in preferred_time_objects]
                                        
                                        # Prevent scheduling in non-preferred time slots
                                        for non_preferred_ts in non_preferred_time_slots:
                                            for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
                                                if (team1_id == team.id or team2_id == team.id) and time_slot_id == non_preferred_ts.id:
                                                    self.model.Add(var == 0)
                            
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            print(f"Error parsing time_preference restriction for team {team.id}: {e}")
                            continue
                
                elif restriction.restriction_type == "court_preference":
                    # Team has court preferences - HARD constraint (only allow preferred court)
                    if restriction.restriction_value:
                        try:
                            restriction_data = json.loads(restriction.restriction_value)
                            
                            if "preferred_court" in restriction_data:
                                preferred_court_name = restriction_data["preferred_court"]
                                preferred_court = next((c for c in courts if c.name == preferred_court_name), None)
                                
                                if preferred_court:
                                    # Block all courts except the preferred one
                                    for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
                                        if (team1_id == team.id or team2_id == team.id) and court_id != preferred_court.id:
                                            self.model.Add(var == 0)
                                            
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            print(f"Error parsing court restriction for team {team.id}: {e}")
                            continue
                
                elif restriction.restriction_type == "tournament_time_preference":
                    # Team has tournament-level time and court preferences - ALL are hard constraints
                    if restriction.restriction_value:
                        try:
                            restriction_data = json.loads(restriction.restriction_value)
                            
                            # Handle earliest_time constraint (hard constraint)
                            if "earliest_time" in restriction_data:
                                earliest_time_str = restriction_data["earliest_time"]
                                # Convert time string to time object for comparison
                                from datetime import time as dt_time
                                earliest_time = dt_time.fromisoformat(earliest_time_str)
                                
                                # Find time slots that start before the earliest time
                                early_time_slots = [ts for ts in time_slots if ts.start_time < earliest_time]
                                
                                # Prevent scheduling in early time slots
                                for early_ts in early_time_slots:
                                    for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
                                        if (team1_id == team.id or team2_id == team.id) and time_slot_id == early_ts.id:
                                            self.model.Add(var == 0)
                            
                            # Handle preferred_court constraint as HARD constraint
                            if "preferred_court" in restriction_data:
                                preferred_court_name = restriction_data["preferred_court"]
                                preferred_court = next((c for c in courts if c.name == preferred_court_name), None)
                                
                                if preferred_court:
                                    # Block all courts except the preferred one
                                    for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
                                        if (team1_id == team.id or team2_id == team.id) and court_id != preferred_court.id:
                                            self.model.Add(var == 0)
                            
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            print(f"Error parsing tournament_time_preference restriction for team {team.id}: {e}")
                            continue
                
                elif restriction.restriction_type == "time_after":
                    # Team can only be scheduled after a specific time (hard constraint)
                    if restriction.restriction_value:
                        try:
                            from datetime import time as dt_time
                            after_time = dt_time.fromisoformat(restriction.restriction_value)
                            
                            # Find time slots that start before the specified time
                            early_time_slots = [ts for ts in time_slots if ts.start_time < after_time]
                            
                            # Prevent scheduling in early time slots
                            for early_ts in early_time_slots:
                                for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
                                    if (team1_id == team.id or team2_id == team.id) and time_slot_id == early_ts.id:
                                        self.model.Add(var == 0)
                                        
                        except (ValueError) as e:
                            print(f"Error parsing time_after restriction for team {team.id}: {e}")
                            continue
                
                elif restriction.restriction_type == "time_before":
                    # Team can only be scheduled before a specific time (hard constraint)
                    if restriction.restriction_value:
                        try:
                            from datetime import time as dt_time
                            before_time = dt_time.fromisoformat(restriction.restriction_value)
                            
                            # Find time slots that start after the specified time
                            late_time_slots = [ts for ts in time_slots if ts.start_time >= before_time]
                            
                            # Prevent scheduling in late time slots
                            for late_ts in late_time_slots:
                                for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
                                    if (team1_id == team.id or team2_id == team.id) and time_slot_id == late_ts.id:
                                        self.model.Add(var == 0)
                                        
                        except (ValueError) as e:
                            print(f"Error parsing time_before restriction for team {team.id}: {e}")
                            continue
                
                elif restriction.restriction_type == "time_range":
                    # Team can only be scheduled within a specific time range (hard constraint)
                    if restriction.restriction_value:
                        try:
                            from datetime import time as dt_time
                            # Parse time range (e.g., "15:00-17:00")
                            start_time_str, end_time_str = restriction.restriction_value.split('-')
                            start_time = dt_time.fromisoformat(start_time_str.strip())
                            end_time = dt_time.fromisoformat(end_time_str.strip())
                            
                            # Find time slots outside the allowed range
                            invalid_time_slots = [ts for ts in time_slots 
                                                if ts.start_time < start_time or ts.start_time >= end_time]
                            
                            # Prevent scheduling in invalid time slots
                            for invalid_ts in invalid_time_slots:
                                for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
                                    if (team1_id == team.id or team2_id == team.id) and time_slot_id == invalid_ts.id:
                                        self.model.Add(var == 0)
                                        
                        except (ValueError, IndexError) as e:
                            print(f"Error parsing time_range restriction for team {team.id}: {e}")
                            continue

    def _add_multi_tournament_rest_constraints(self, match_vars: Dict, all_teams: List[Team], time_slots: List[TimeSlot]):
        """Add constraints to ensure teams playing in multiple tournaments have at least 1 hour rest between games"""
        from datetime import timedelta
        
        # Group teams by name to find teams playing in multiple tournaments
        teams_by_name = {}
        for team in all_teams:
            if team.name not in teams_by_name:
                teams_by_name[team.name] = []
            teams_by_name[team.name].append(team)
        
        # Find teams that play in multiple tournaments
        multi_tournament_teams = {name: teams for name, teams in teams_by_name.items() if len(teams) > 1}
        
        for team_name, teams in multi_tournament_teams.items():
            print(f"Processing multi-tournament team: {team_name} with {len(teams)} teams")
            
            # Get all possible matches for this team across all tournaments
            team_matches = []
            for team in teams:
                for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
                    if team1_id == team.id or team2_id == team.id:
                        time_slot = next((ts for ts in time_slots if ts.id == time_slot_id), None)
                        if time_slot:
                            team_matches.append((var, time_slot, team1_id, team2_id))
            
            print(f"Found {len(team_matches)} possible matches for {team_name}")
            
            # Group matches by time slot to avoid duplicate constraints
            matches_by_time = {}
            for var, time_slot, team1_id, team2_id in team_matches:
                time_key = time_slot.start_time
                if time_key not in matches_by_time:
                    matches_by_time[time_key] = []
                matches_by_time[time_key].append((var, team1_id, team2_id))
            
            # Add constraints only between different time slots
            constraints_added = 0
            time_slots_list = sorted(matches_by_time.keys())
            
            for i, time1 in enumerate(time_slots_list):
                for j, time2 in enumerate(time_slots_list):
                    if i != j:  # Different time slots
                        time_diff = self._calculate_time_difference(time1, time2)
                        
                        # If time difference is less than or equal to 1 hour, they can't both be scheduled
                        if time_diff <= 60:  # 60 minutes = 1 hour (inclusive)
                            # Add constraint between all matches at these two time slots
                            for var1, team1_id_1, team2_id_1 in matches_by_time[time1]:
                                for var2, team1_id_2, team2_id_2 in matches_by_time[time2]:
                                    self.model.Add(var1 + var2 <= 1)
                                    constraints_added += 1
            
            print(f"Added {constraints_added} constraints for {team_name}")
        
        print(f"Applied multi-tournament rest constraints for {len(multi_tournament_teams)} teams playing in multiple tournaments")
    
    def _add_multi_tournament_rest_constraints_optimized(self, match_vars: Dict, all_teams: List[Team], time_slots: List[TimeSlot]):
        """Optimized version: Add constraints to ensure teams playing in multiple tournaments have at least 1 hour rest between games"""
        
        # Group teams by name to find teams playing in multiple tournaments
        teams_by_name = {}
        for team in all_teams:
            if team.name not in teams_by_name:
                teams_by_name[team.name] = []
            teams_by_name[team.name].append(team)
        
        # Find teams that play in multiple tournaments
        multi_tournament_teams = {name: teams for name, teams in teams_by_name.items() if len(teams) > 1}
        
        for team_name, teams in multi_tournament_teams.items():
            print(f"Processing multi-tournament team: {team_name} with {len(teams)} teams")
            
            # Get all possible matches for this team across all tournaments
            team_matches = []
            for team in teams:
                for (team1_id, team2_id, court_id, time_slot_id), var in match_vars.items():
                    if team1_id == team.id or team2_id == team.id:
                        time_slot = next((ts for ts in time_slots if ts.id == time_slot_id), None)
                        if time_slot:
                            team_matches.append((var, time_slot))
            
            print(f"Found {len(team_matches)} possible matches for {team_name}")
            
            # Create a more efficient constraint: for each time slot, 
            # ensure the team can only play in at most one match
            time_slot_vars = {}
            for var, time_slot in team_matches:
                time_key = time_slot.start_time
                if time_key not in time_slot_vars:
                    time_slot_vars[time_key] = []
                time_slot_vars[time_key].append(var)
            
            # For each time slot, add constraint that at most one match can be scheduled
            constraints_added = 0
            for time_key, vars_list in time_slot_vars.items():
                if len(vars_list) > 1:
                    # At most one match can be scheduled at this time
                    self.model.Add(sum(vars_list) <= 1)
                    constraints_added += 1
            
            # Add constraints only between adjacent time slots (within 1 hour)
            time_slots_list = sorted(time_slot_vars.keys())
            for i in range(len(time_slots_list) - 1):
                time1 = time_slots_list[i]
                time2 = time_slots_list[i + 1]
                time_diff = self._calculate_time_difference(time1, time2)
                
                if time_diff <= 60:  # Within 1 hour
                    # Can't play in both time slots - use a single constraint for all combinations
                    vars1 = time_slot_vars[time1]
                    vars2 = time_slot_vars[time2]
                    # Add constraint: sum of all matches in time1 + sum of all matches in time2 <= 1
                    self.model.Add(sum(vars1) + sum(vars2) <= 1)
                    constraints_added += 1
            
            print(f"Added {constraints_added} constraints for {team_name}")
        
        print(f"Applied optimized multi-tournament rest constraints for {len(multi_tournament_teams)} teams playing in multiple tournaments")
    
    def _calculate_time_difference(self, time1, time2):
        """Calculate time difference in minutes between two time objects"""
        from datetime import datetime, date
        
        # Create datetime objects for comparison (using same date)
        dt1 = datetime.combine(date.today(), time1)
        dt2 = datetime.combine(date.today(), time2)
        
        # Calculate absolute difference in minutes
        diff = abs((dt2 - dt1).total_seconds() / 60)
        return diff
