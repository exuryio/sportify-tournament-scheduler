-- Sunday Tournaments Data for Sportify
-- Maxi 40 Masculino, Maxi 50 Masculino, Maxi 50 Femenino

-- Insert Sunday tournaments
INSERT INTO tournaments (id, name, description, sport_type, start_date, end_date, max_teams) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Maxi 40 Masculino', 'Torneo: Maxi 40 Masculino - Domingo', 'basketball', '2025-09-01', '2025-12-31', 12),
('550e8400-e29b-41d4-a716-446655440002', 'Maxi 50 Masculino', 'Torneo: Maxi 50 Masculino - Domingo', 'basketball', '2025-09-01', '2025-12-31', 10),
('550e8400-e29b-41d4-a716-446655440003', 'Maxi 50 Femenino', 'Torneo: Maxi 50 Femenino - Domingo', 'basketball', '2025-09-01', '2025-12-31', 8);

-- Insert Sunday time slots (day_of_week = 0 for Sunday)
INSERT INTO time_slots (id, day_of_week, start_time, end_time) VALUES
('550e8400-e29b-41d4-a716-446655440010', 0, '09:00:00', '10:00:00'),
('550e8400-e29b-41d4-a716-446655440011', 0, '10:15:00', '11:15:00'),
('550e8400-e29b-41d4-a716-446655440012', 0, '11:30:00', '12:30:00'),
('550e8400-e29b-41d4-a716-446655440013', 0, '12:45:00', '13:45:00'),
('550e8400-e29b-41d4-a716-446655440014', 0, '14:00:00', '15:00:00'),
('550e8400-e29b-41d4-a716-446655440015', 0, '15:15:00', '16:15:00');

-- Maxi 40 Masculino Teams (12 teams)
INSERT INTO teams (id, tournament_id, name, captain_name, captain_email, captain_phone, preferred_days) VALUES
('550e8400-e29b-41d4-a716-446655440100', '550e8400-e29b-41d4-a716-446655440001', 'Titanes', 'Capitán Titanes', 'capitan.titanes@example.com', '+12345678901', '{0}'),
('550e8400-e29b-41d4-a716-446655440101', '550e8400-e29b-41d4-a716-446655440001', 'Leones', 'Capitán Leones', 'capitan.leones@example.com', '+12345678902', '{0}'),
('550e8400-e29b-41d4-a716-446655440102', '550e8400-e29b-41d4-a716-446655440001', 'Eagles', 'Capitán Eagles', 'capitan.eagles@example.com', '+12345678903', '{0}'),
('550e8400-e29b-41d4-a716-446655440103', '550e8400-e29b-41d4-a716-446655440001', 'Sharks', 'Capitán Sharks', 'capitan.sharks@example.com', '+12345678904', '{0}'),
('550e8400-e29b-41d4-a716-446655440104', '550e8400-e29b-41d4-a716-446655440001', 'Wolves', 'Capitán Wolves', 'capitan.wolves@example.com', '+12345678905', '{0}'),
('550e8400-e29b-41d4-a716-446655440105', '550e8400-e29b-41d4-a716-446655440001', 'Bulls', 'Capitán Bulls', 'capitan.bulls@example.com', '+12345678906', '{0}'),
('550e8400-e29b-41d4-a716-446655440106', '550e8400-e29b-41d4-a716-446655440001', 'Hawks', 'Capitán Hawks', 'capitan.hawks@example.com', '+12345678907', '{0}'),
('550e8400-e29b-41d4-a716-446655440107', '550e8400-e29b-41d4-a716-446655440001', 'Panthers', 'Capitán Panthers', 'capitan.panthers@example.com', '+12345678908', '{0}'),
('550e8400-e29b-41d4-a716-446655440108', '550e8400-e29b-41d4-a716-446655440001', 'Tigers', 'Capitán Tigers', 'capitan.tigers@example.com', '+12345678909', '{0}'),
('550e8400-e29b-41d4-a716-446655440109', '550e8400-e29b-41d4-a716-446655440001', 'Bears', 'Capitán Bears', 'capitan.bears@example.com', '+12345678910', '{0}'),
('550e8400-e29b-41d4-a716-446655440110', '550e8400-e29b-41d4-a716-446655440001', 'Lions', 'Capitán Lions', 'capitan.lions@example.com', '+12345678911', '{0}'),
('550e8400-e29b-41d4-a716-446655440111', '550e8400-e29b-41d4-a716-446655440001', 'Falcons', 'Capitán Falcons', 'capitan.falcons@example.com', '+12345678912', '{0}');

-- Maxi 50 Masculino Teams (10 teams)
INSERT INTO teams (id, tournament_id, name, captain_name, captain_email, captain_phone, preferred_days) VALUES
('550e8400-e29b-41d4-a716-446655440200', '550e8400-e29b-41d4-a716-446655440002', 'Veteranos', 'Capitán Veteranos', 'capitan.veteranos@example.com', '+12345678913', '{0}'),
('550e8400-e29b-41d4-a716-446655440201', '550e8400-e29b-41d4-a716-446655440002', 'Legends', 'Capitán Legends', 'capitan.legends@example.com', '+12345678914', '{0}'),
('550e8400-e29b-41d4-a716-446655440202', '550e8400-e29b-41d4-a716-446655440002', 'Masters', 'Capitán Masters', 'capitan.masters@example.com', '+12345678915', '{0}'),
('550e8400-e29b-41d4-a716-446655440203', '550e8400-e29b-41d4-a716-446655440002', 'Seniors', 'Capitán Seniors', 'capitan.seniors@example.com', '+12345678916', '{0}'),
('550e8400-e29b-41d4-a716-446655440204', '550e8400-e29b-41d4-a716-446655440002', 'Golden', 'Capitán Golden', 'capitan.golden@example.com', '+12345678917', '{0}'),
('550e8400-e29b-41d4-a716-446655440205', '550e8400-e29b-41d4-a716-446655440002', 'Classic', 'Capitán Classic', 'capitan.classic@example.com', '+12345678918', '{0}'),
('550e8400-e29b-41d4-a716-446655440206', '550e8400-e29b-41d4-a716-446655440002', 'Elite', 'Capitán Elite', 'capitan.elite@example.com', '+12345678919', '{0}'),
('550e8400-e29b-41d4-a716-446655440207', '550e8400-e29b-41d4-a716-446655440002', 'Prime', 'Capitán Prime', 'capitan.prime@example.com', '+12345678920', '{0}'),
('550e8400-e29b-41d4-a716-446655440208', '550e8400-e29b-41d4-a716-446655440002', 'Vintage', 'Capitán Vintage', 'capitan.vintage@example.com', '+12345678921', '{0}'),
('550e8400-e29b-41d4-a716-446655440209', '550e8400-e29b-41d4-a716-446655440002', 'Noble', 'Capitán Noble', 'capitan.noble@example.com', '+12345678922', '{0}');

-- Maxi 50 Femenino Teams (8 teams)
INSERT INTO teams (id, tournament_id, name, captain_name, captain_email, captain_phone, preferred_days) VALUES
('550e8400-e29b-41d4-a716-446655440300', '550e8400-e29b-41d4-a716-446655440003', 'Diamantes', 'Capitán Diamantes', 'capitan.diamantes@example.com', '+12345678923', '{0}'),
('550e8400-e29b-41d4-a716-446655440301', '550e8400-e29b-41d4-a716-446655440003', 'Perlas', 'Capitán Perlas', 'capitan.perlas@example.com', '+12345678924', '{0}'),
('550e8400-e29b-41d4-a716-446655440302', '550e8400-e29b-41d4-a716-446655440003', 'Rubies', 'Capitán Rubies', 'capitan.rubies@example.com', '+12345678925', '{0}'),
('550e8400-e29b-41d4-a716-446655440303', '550e8400-e29b-41d4-a716-446655440003', 'Esmeraldas', 'Capitán Esmeraldas', 'capitan.esmeraldas@example.com', '+12345678926', '{0}'),
('550e8400-e29b-41d4-a716-446655440304', '550e8400-e29b-41d4-a716-446655440003', 'Zafiros', 'Capitán Zafiros', 'capitan.zafiros@example.com', '+12345678927', '{0}'),
('550e8400-e29b-41d4-a716-446655440305', '550e8400-e29b-41d4-a716-446655440003', 'Topacios', 'Capitán Topacios', 'capitan.topacios@example.com', '+12345678928', '{0}'),
('550e8400-e29b-41d4-a716-446655440306', '550e8400-e29b-41d4-a716-446655440003', 'Amatistas', 'Capitán Amatistas', 'capitan.amatistas@example.com', '+12345678929', '{0}'),
('550e8400-e29b-41d4-a716-446655440307', '550e8400-e29b-41d4-a716-446655440003', 'Cristales', 'Capitán Cristales', 'capitan.cristales@example.com', '+12345678930', '{0}');
