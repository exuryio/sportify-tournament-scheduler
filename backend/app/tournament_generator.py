from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from app.models import (
    Tournament, Team, TournamentRound, TournamentGroup, 
    TournamentFixture, TournamentStanding
)
import uuid
import itertools

class TournamentFixtureGenerator:
    """Generator for tournament fixtures and rounds"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_tournament_structure(self, tournament_id: str, preserve_scores: bool = False) -> Dict:
        """Generate complete tournament structure based on team count"""
        tournament = self.db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            raise ValueError("Tournament not found")
        
        teams = self.db.query(Team).filter(
            Team.tournament_id == tournament_id,
            Team.is_active == True
        ).all()
        
        if len(teams) < 4:
            raise ValueError("Tournament needs at least 4 teams")
        
        team_count = len(teams)
        
        # Check if fixtures already exist
        existing_fixtures = self.db.query(TournamentFixture).join(TournamentRound).filter(
            TournamentRound.tournament_id == tournament_id
        ).all()
        
        has_existing_scores = any((fixture.team1_score is not None and fixture.team1_score > 0) or 
                                 (fixture.team2_score is not None and fixture.team2_score > 0)
                                for fixture in existing_fixtures)
        
        if has_existing_scores and not preserve_scores:
            return {
                "warning": "existing_scores",
                "message": "Este torneo ya tiene resultados guardados. ¿Estás seguro de que quieres regenerar la estructura y perder todos los resultados?",
                "has_existing_scores": True
            }
        
        # Clear existing tournament structure (preserving scores if requested)
        self._clear_tournament_structure(tournament_id, preserve_scores)
        
        # Generate rounds based on team count
        rounds_created = []
        
        # Round 1: All teams play against all teams (round robin)
        round1 = self._create_round_1(tournament_id, teams)
        rounds_created.append(round1)
        
        # Determine qualification rules
        if team_count >= 13:
            # Top 10 teams qualify, split into 2 groups of 5
            qualifying_teams = 10
            group_size = 5
        else:
            # Top 8 teams qualify, split into 2 groups of 4
            qualifying_teams = 8
            group_size = 4
        
        # Round 2: Group stage
        round2 = self._create_round_2(tournament_id, qualifying_teams, group_size)
        rounds_created.append(round2)
        
        # Round 3: Semifinals
        round3 = self._create_semifinals(tournament_id)
        rounds_created.append(round3)
        
        # Round 4: Third place match
        round4 = self._create_third_place(tournament_id)
        rounds_created.append(round4)
        
        # Round 5: Final
        round5 = self._create_final(tournament_id)
        rounds_created.append(round5)
        
        self.db.commit()
        
        return {
            "tournament_id": tournament_id,
            "team_count": team_count,
            "qualifying_teams": qualifying_teams,
            "group_size": group_size,
            "rounds_created": len(rounds_created),
            "rounds": rounds_created
        }
    
    def _clear_tournament_structure(self, tournament_id: str, preserve_scores: bool = False):
        """Clear existing tournament structure"""
        # Get all rounds for this tournament
        rounds = self.db.query(TournamentRound).filter(
            TournamentRound.tournament_id == tournament_id
        ).all()
        
        for round_obj in rounds:
            # Delete standings
            standings = self.db.query(TournamentStanding).join(TournamentGroup).filter(
                TournamentGroup.tournament_round_id == round_obj.id
            ).all()
            for standing in standings:
                self.db.delete(standing)
            
            # Delete fixtures (preserve scores if requested)
            fixtures = self.db.query(TournamentFixture).filter(
                TournamentFixture.tournament_round_id == round_obj.id
            ).all()
            for fixture in fixtures:
                self.db.delete(fixture)
            
            # Delete groups
            groups = self.db.query(TournamentGroup).filter(
                TournamentGroup.tournament_round_id == round_obj.id
            ).all()
            for group in groups:
                self.db.delete(group)
            
            # Delete round
            self.db.delete(round_obj)
        
        self.db.commit()
    
    def _create_round_1(self, tournament_id: str, teams: List[Team]) -> Dict:
        """Create Round 1: All teams play against all teams"""
        round1 = TournamentRound(
            tournament_id=tournament_id,
            round_number=1,
            round_name="Primera Ronda",
            round_type="group_stage",
            status="pending"
        )
        self.db.add(round1)
        self.db.flush()  # Get the ID
        
        # Create all possible match combinations
        fixtures = []
        match_order = 1
        
        for team1, team2 in itertools.combinations(teams, 2):
            fixture = TournamentFixture(
                tournament_round_id=round1.id,
                team1_id=team1.id,
                team2_id=team2.id,
                fixture_type="group_match",
                match_order=match_order,
                status="pending"
            )
            self.db.add(fixture)
            fixtures.append(fixture)
            match_order += 1
        
        self.db.flush()
        
        return {
            "round_id": str(round1.id),
            "round_name": round1.round_name,
            "fixtures_count": len(fixtures),
            "fixtures": [{"id": str(f.id), "team1": f.team1_id, "team2": f.team2_id} for f in fixtures]
        }
    
    def _create_round_2(self, tournament_id: str, qualifying_teams: int, group_size: int) -> Dict:
        """Create Round 2: Group stage with qualifying teams"""
        round2 = TournamentRound(
            tournament_id=tournament_id,
            round_number=2,
            round_name="Segunda Ronda",
            round_type="group_stage",
            status="pending"
        )
        self.db.add(round2)
        self.db.flush()
        
        # Create two groups
        group_a = TournamentGroup(
            tournament_round_id=round2.id,
            group_name="Grupo A",
            group_order=1
        )
        group_b = TournamentGroup(
            tournament_round_id=round2.id,
            group_name="Grupo B",
            group_order=2
        )
        self.db.add_all([group_a, group_b])
        self.db.flush()
        
        # Note: Actual team assignment will happen after Round 1 results
        # For now, we just create the group structure
        
        return {
            "round_id": str(round2.id),
            "round_name": round2.round_name,
            "groups": [
                {"id": str(group_a.id), "name": group_a.group_name},
                {"id": str(group_b.id), "name": group_b.group_name}
            ],
            "qualifying_teams": qualifying_teams,
            "group_size": group_size
        }
    
    def _create_semifinals(self, tournament_id: str) -> Dict:
        """Create Round 3: Semifinals"""
        round3 = TournamentRound(
            tournament_id=tournament_id,
            round_number=3,
            round_name="Semifinales",
            round_type="knockout",
            status="pending"
        )
        self.db.add(round3)
        self.db.flush()
        
        # Create semifinal fixtures
        # Semifinal 1: 1st Group A vs 2nd Group B
        semifinal1 = TournamentFixture(
            tournament_round_id=round3.id,
            team1_id=None,  # Will be filled after Round 2
            team2_id=None,  # Will be filled after Round 2
            fixture_type="semifinal",
            match_order=1,
            status="pending"
        )
        
        # Semifinal 2: 2nd Group A vs 1st Group B
        semifinal2 = TournamentFixture(
            tournament_round_id=round3.id,
            team1_id=None,  # Will be filled after Round 2
            team2_id=None,  # Will be filled after Round 2
            fixture_type="semifinal",
            match_order=2,
            status="pending"
        )
        
        self.db.add_all([semifinal1, semifinal2])
        self.db.flush()
        
        return {
            "round_id": str(round3.id),
            "round_name": round3.round_name,
            "fixtures_count": 2,
            "fixtures": [
                {"id": str(semifinal1.id), "description": "1º Grupo A vs 2º Grupo B"},
                {"id": str(semifinal2.id), "description": "2º Grupo A vs 1º Grupo B"}
            ]
        }
    
    def _create_third_place(self, tournament_id: str) -> Dict:
        """Create Round 4: Third place match"""
        round4 = TournamentRound(
            tournament_id=tournament_id,
            round_number=4,
            round_name="Tercer Lugar",
            round_type="knockout",
            status="pending"
        )
        self.db.add(round4)
        self.db.flush()
        
        # Create third place fixture
        third_place = TournamentFixture(
            tournament_round_id=round4.id,
            team1_id=None,  # Will be filled after semifinals
            team2_id=None,  # Will be filled after semifinals
            fixture_type="third_place",
            match_order=1,
            status="pending"
        )
        
        self.db.add(third_place)
        self.db.flush()
        
        return {
            "round_id": str(round4.id),
            "round_name": round4.round_name,
            "fixtures_count": 1,
            "fixtures": [
                {"id": str(third_place.id), "description": "Perdedor Semifinal 1 vs Perdedor Semifinal 2"}
            ]
        }
    
    def _create_final(self, tournament_id: str) -> Dict:
        """Create Round 5: Final"""
        round5 = TournamentRound(
            tournament_id=tournament_id,
            round_number=5,
            round_name="Final",
            round_type="final",
            status="pending"
        )
        self.db.add(round5)
        self.db.flush()
        
        # Create final fixture
        final = TournamentFixture(
            tournament_round_id=round5.id,
            team1_id=None,  # Will be filled after semifinals
            team2_id=None,  # Will be filled after semifinals
            fixture_type="final",
            match_order=1,
            status="pending"
        )
        
        self.db.add(final)
        self.db.flush()
        
        return {
            "round_id": str(round5.id),
            "round_name": round5.round_name,
            "fixtures_count": 1,
            "fixtures": [
                {"id": str(final.id), "description": "Ganador Semifinal 1 vs Ganador Semifinal 2"}
            ]
        }
    
    def get_tournament_fixtures(self, tournament_id: str) -> Dict:
        """Get all fixtures for a tournament organized by rounds"""
        rounds = self.db.query(TournamentRound).filter(
            TournamentRound.tournament_id == tournament_id
        ).order_by(TournamentRound.round_number).all()
        
        result = {
            "tournament_id": tournament_id,
            "rounds": []
        }
        
        for round_obj in rounds:
            round_data = {
                "round_id": str(round_obj.id),
                "round_number": round_obj.round_number,
                "round_name": round_obj.round_name,
                "round_type": round_obj.round_type,
                "status": round_obj.status,
                "groups": [],
                "fixtures": []
            }
            
            # Get groups for this round
            groups = self.db.query(TournamentGroup).filter(
                TournamentGroup.tournament_round_id == round_obj.id
            ).order_by(TournamentGroup.group_order).all()
            
            for group in groups:
                group_data = {
                    "group_id": str(group.id),
                    "group_name": group.group_name,
                    "group_order": group.group_order,
                    "fixtures": [],
                    "standings": []
                }
                
                # Get fixtures for this group
                fixtures = self.db.query(TournamentFixture).filter(
                    TournamentFixture.tournament_group_id == group.id
                ).order_by(TournamentFixture.match_order).all()
                
                for fixture in fixtures:
                    team1 = self.db.query(Team).filter(Team.id == fixture.team1_id).first()
                    team2 = self.db.query(Team).filter(Team.id == fixture.team2_id).first()
                    
                    fixture_data = {
                        "fixture_id": str(fixture.id),
                        "team1": {
                            "id": str(fixture.team1_id),
                            "name": team1.name if team1 else "TBD"
                        },
                        "team2": {
                            "id": str(fixture.team2_id),
                            "name": team2.name if team2 else "TBD"
                        },
                        "team1_score": fixture.team1_score,
                        "team2_score": fixture.team2_score,
                        "status": fixture.status,
                        "match_order": fixture.match_order
                    }
                    group_data["fixtures"].append(fixture_data)
                
                # Get standings for this group
                standings = self.db.query(TournamentStanding).filter(
                    TournamentStanding.tournament_group_id == group.id
                ).order_by(TournamentStanding.position).all()
                
                for standing in standings:
                    team = self.db.query(Team).filter(Team.id == standing.team_id).first()
                    standing_data = {
                        "team_id": str(standing.team_id),
                        "team_name": team.name if team else "Unknown",
                        "matches_played": standing.matches_played,
                        "wins": standing.wins,
                        "losses": standing.losses,
                        "points_for": standing.points_for,
                        "points_against": standing.points_against,
                        "points_difference": standing.points_difference,
                        "position": standing.position
                    }
                    group_data["standings"].append(standing_data)
                
                round_data["groups"].append(group_data)
            
            # Get fixtures not in groups (knockout rounds)
            non_group_fixtures = self.db.query(TournamentFixture).filter(
                TournamentFixture.tournament_round_id == round_obj.id,
                TournamentFixture.tournament_group_id.is_(None)
            ).order_by(TournamentFixture.match_order).all()
            
            for fixture in non_group_fixtures:
                team1 = self.db.query(Team).filter(Team.id == fixture.team1_id).first() if fixture.team1_id else None
                team2 = self.db.query(Team).filter(Team.id == fixture.team2_id).first() if fixture.team2_id else None
                
                fixture_data = {
                    "fixture_id": str(fixture.id),
                    "team1": {
                        "id": str(fixture.team1_id) if fixture.team1_id else None,
                        "name": team1.name if team1 else "TBD"
                    },
                    "team2": {
                        "id": str(fixture.team2_id) if fixture.team2_id else None,
                        "name": team2.name if team2 else "TBD"
                    },
                    "team1_score": fixture.team1_score,
                    "team2_score": fixture.team2_score,
                    "status": fixture.status,
                    "match_order": fixture.match_order,
                    "fixture_type": fixture.fixture_type
                }
                round_data["fixtures"].append(fixture_data)
            
            result["rounds"].append(round_data)
        
        return result
