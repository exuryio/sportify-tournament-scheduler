-- Sportify Database Initialization Script

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tournaments table
CREATE TABLE IF NOT EXISTS tournaments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sport_type VARCHAR(100) DEFAULT 'basketball',
    start_date DATE,
    end_date DATE,
    max_teams INTEGER DEFAULT 16,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Courts table
CREATE TABLE IF NOT EXISTS courts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    capacity INTEGER DEFAULT 20,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Time slots table
CREATE TABLE IF NOT EXISTS time_slots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6), -- 0=Sunday, 1=Monday, etc.
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(day_of_week, start_time)
);

-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tournament_id UUID REFERENCES tournaments(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    captain_name VARCHAR(255),
    captain_email VARCHAR(255),
    captain_phone VARCHAR(50),
    earliest_start_time TIME DEFAULT '09:00:00',
    latest_start_time TIME DEFAULT '22:00:00',
    preferred_days INTEGER[] DEFAULT '{1,2,3,4,5}', -- Monday to Friday
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Matches table
CREATE TABLE IF NOT EXISTS matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tournament_id UUID REFERENCES tournaments(id) ON DELETE CASCADE,
    team1_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    team2_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    court_id UUID REFERENCES courts(id) ON DELETE SET NULL,
    time_slot_id UUID REFERENCES time_slots(id) ON DELETE SET NULL,
    scheduled_date DATE,
    scheduled_time TIME,
    status VARCHAR(50) DEFAULT 'scheduled', -- scheduled, completed, cancelled
    score_team1 INTEGER DEFAULT 0,
    score_team2 INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Schedules table
CREATE TABLE IF NOT EXISTS schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tournament_id UUID REFERENCES tournaments(id) ON DELETE CASCADE,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'draft', -- draft, published, archived
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Schedule matches junction table
CREATE TABLE IF NOT EXISTS schedule_matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schedule_id UUID REFERENCES schedules(id) ON DELETE CASCADE,
    match_id UUID REFERENCES matches(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Team restrictions table for specific scheduling constraints
CREATE TABLE IF NOT EXISTS team_restrictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    restriction_date DATE NOT NULL, -- The Saturday date this restriction applies to
    restriction_type VARCHAR(50) NOT NULL, -- 'not_scheduled', 'time_preference', 'court_preference', 'tournament_time_preference'
    restriction_value TEXT, -- JSON string with specific constraints
    notes TEXT, -- Additional notes from organizer
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, restriction_date, restriction_type)
);

-- Tournament rounds table
CREATE TABLE IF NOT EXISTS tournament_rounds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tournament_id UUID REFERENCES tournaments(id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL, -- 1, 2, 3, 4, 5 (1st round, 2nd round, semifinals, 3rd place, final)
    round_name VARCHAR(100) NOT NULL, -- 'Primera Ronda', 'Segunda Ronda', 'Semifinales', 'Tercer Lugar', 'Final'
    round_type VARCHAR(50) NOT NULL, -- 'group_stage', 'knockout', 'final'
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tournament_id, round_number)
);

-- Tournament groups table (for 2nd round)
CREATE TABLE IF NOT EXISTS tournament_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tournament_round_id UUID REFERENCES tournament_rounds(id) ON DELETE CASCADE,
    group_name VARCHAR(50) NOT NULL, -- 'Grupo A', 'Grupo B'
    group_order INTEGER NOT NULL, -- 1, 2
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tournament_round_id, group_name)
);

-- Tournament fixtures table
CREATE TABLE IF NOT EXISTS tournament_fixtures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tournament_round_id UUID REFERENCES tournament_rounds(id) ON DELETE CASCADE,
    tournament_group_id UUID REFERENCES tournament_groups(id) ON DELETE SET NULL,
    team1_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    team2_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    match_id UUID REFERENCES matches(id) ON DELETE SET NULL, -- Link to actual match if scheduled
    fixture_type VARCHAR(50) NOT NULL, -- 'group_match', 'semifinal', 'third_place', 'final'
    match_order INTEGER, -- Order within the round/group
    team1_score INTEGER DEFAULT 0,
    team2_score INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'scheduled', 'completed'
    last_updated_by VARCHAR(255), -- Who last updated the scores
    last_updated_at TIMESTAMP WITH TIME ZONE, -- When scores were last updated
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tournament standings table (for group stages)
CREATE TABLE IF NOT EXISTS tournament_standings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tournament_group_id UUID REFERENCES tournament_groups(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    matches_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    points_for INTEGER DEFAULT 0,
    points_against INTEGER DEFAULT 0,
    points_difference INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0, -- Tournament points (2 for win, 1 for loss, 0 for forfeit)
    position INTEGER, -- Final position in group
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tournament_group_id, team_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_teams_tournament_id ON teams(tournament_id);
CREATE INDEX IF NOT EXISTS idx_matches_tournament_id ON matches(tournament_id);
CREATE INDEX IF NOT EXISTS idx_matches_team1_id ON matches(team1_id);
CREATE INDEX IF NOT EXISTS idx_matches_team2_id ON matches(team2_id);
CREATE INDEX IF NOT EXISTS idx_matches_court_id ON matches(court_id);
CREATE INDEX IF NOT EXISTS idx_matches_time_slot_id ON matches(time_slot_id);
CREATE INDEX IF NOT EXISTS idx_schedules_tournament_id ON schedules(tournament_id);
CREATE INDEX IF NOT EXISTS idx_schedule_matches_schedule_id ON schedule_matches(schedule_id);
CREATE INDEX IF NOT EXISTS idx_team_restrictions_team_id ON team_restrictions(team_id);
CREATE INDEX IF NOT EXISTS idx_team_restrictions_date ON team_restrictions(restriction_date);
CREATE INDEX IF NOT EXISTS idx_tournament_rounds_tournament_id ON tournament_rounds(tournament_id);
CREATE INDEX IF NOT EXISTS idx_tournament_groups_round_id ON tournament_groups(tournament_round_id);
CREATE INDEX IF NOT EXISTS idx_tournament_fixtures_round_id ON tournament_fixtures(tournament_round_id);
CREATE INDEX IF NOT EXISTS idx_tournament_fixtures_group_id ON tournament_fixtures(tournament_group_id);
CREATE INDEX IF NOT EXISTS idx_tournament_standings_group_id ON tournament_standings(tournament_group_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_tournaments_updated_at BEFORE UPDATE ON tournaments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_matches_updated_at BEFORE UPDATE ON matches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_schedules_updated_at BEFORE UPDATE ON schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_team_restrictions_updated_at BEFORE UPDATE ON team_restrictions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tournament_rounds_updated_at BEFORE UPDATE ON tournament_rounds
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tournament_fixtures_updated_at BEFORE UPDATE ON tournament_fixtures
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tournament_standings_updated_at BEFORE UPDATE ON tournament_standings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
