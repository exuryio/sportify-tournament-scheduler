-- Update Sunday Tournaments with Correct Team Names
-- Based on user provided data

-- Update tournament max_teams to match actual team counts
UPDATE tournaments SET max_teams = 10 WHERE id = '550e8400-e29b-41d4-a716-446655440001'; -- Maxi 40 Masculino
UPDATE tournaments SET max_teams = 12 WHERE id = '550e8400-e29b-41d4-a716-446655440002'; -- Maxi 50 Masculino
UPDATE tournaments SET max_teams = 15 WHERE id = '550e8400-e29b-41d4-a716-446655440003'; -- Maxi 50 Femenino

-- First, delete existing teams for Sunday tournaments
DELETE FROM teams WHERE tournament_id IN (
    '550e8400-e29b-41d4-a716-446655440001', -- Maxi 40 Masculino
    '550e8400-e29b-41d4-a716-446655440002', -- Maxi 50 Masculino  
    '550e8400-e29b-41d4-a716-446655440003'  -- Maxi 50 Femenino
);

-- Maxi 40 Masculino Teams (10 teams)
INSERT INTO teams (id, tournament_id, name, captain_name, captain_email, captain_phone, preferred_days) VALUES
('550e8400-e29b-41d4-a716-446655440100', '550e8400-e29b-41d4-a716-446655440001', 'Brother Hood', 'Capitán Brother Hood', 'capitan.brotherhood@example.com', '+12345678901', '{0}'),
('550e8400-e29b-41d4-a716-446655440101', '550e8400-e29b-41d4-a716-446655440001', 'Sharks', 'Capitán Sharks', 'capitan.sharks@example.com', '+12345678902', '{0}'),
('550e8400-e29b-41d4-a716-446655440102', '550e8400-e29b-41d4-a716-446655440001', 'Coyotes', 'Capitán Coyotes', 'capitan.coyotes@example.com', '+12345678903', '{0}'),
('550e8400-e29b-41d4-a716-446655440103', '550e8400-e29b-41d4-a716-446655440001', 'La Union', 'Capitán La Union', 'capitan.launion@example.com', '+12345678904', '{0}'),
('550e8400-e29b-41d4-a716-446655440104', '550e8400-e29b-41d4-a716-446655440001', 'Warriors Tintal', 'Capitán Warriors Tintal', 'capitan.warriorstintal@example.com', '+12345678905', '{0}'),
('550e8400-e29b-41d4-a716-446655440105', '550e8400-e29b-41d4-a716-446655440001', '7 Canchas', 'Capitán 7 Canchas', 'capitan.7canchas@example.com', '+12345678906', '{0}'),
('550e8400-e29b-41d4-a716-446655440106', '550e8400-e29b-41d4-a716-446655440001', 'Sportr', 'Capitán Sportr', 'capitan.sportr@example.com', '+12345678907', '{0}'),
('550e8400-e29b-41d4-a716-446655440107', '550e8400-e29b-41d4-a716-446655440001', 'Leader', 'Capitán Leader', 'capitan.leader@example.com', '+12345678908', '{0}'),
('550e8400-e29b-41d4-a716-446655440108', '550e8400-e29b-41d4-a716-446655440001', 'Gators', 'Capitán Gators', 'capitan.gators@example.com', '+12345678909', '{0}'),
('550e8400-e29b-41d4-a716-446655440109', '550e8400-e29b-41d4-a716-446655440001', 'Rehco', 'Capitán Rehco', 'capitan.rehco@example.com', '+12345678910', '{0}');

-- Maxi 50 Masculino Teams (12 teams)
INSERT INTO teams (id, tournament_id, name, captain_name, captain_email, captain_phone, preferred_days) VALUES
('550e8400-e29b-41d4-a716-446655440200', '550e8400-e29b-41d4-a716-446655440002', 'Nest''s', 'Capitán Nest''s', 'capitan.nests@example.com', '+12345678911', '{0}'),
('550e8400-e29b-41d4-a716-446655440201', '550e8400-e29b-41d4-a716-446655440002', 'Raptor', 'Capitán Raptor', 'capitan.raptor@example.com', '+12345678912', '{0}'),
('550e8400-e29b-41d4-a716-446655440202', '550e8400-e29b-41d4-a716-446655440002', 'Sport', 'Capitán Sport', 'capitan.sport@example.com', '+12345678913', '{0}'),
('550e8400-e29b-41d4-a716-446655440203', '550e8400-e29b-41d4-a716-446655440002', 'Fenix', 'Capitán Fenix', 'capitan.fenix@example.com', '+12345678914', '{0}'),
('550e8400-e29b-41d4-a716-446655440204', '550e8400-e29b-41d4-a716-446655440002', 'Halcones', 'Capitán Halcones', 'capitan.halcones@example.com', '+12345678915', '{0}'),
('550e8400-e29b-41d4-a716-446655440205', '550e8400-e29b-41d4-a716-446655440002', 'Brincosaurios', 'Capitán Brincosaurios', 'capitan.brincosaurios@example.com', '+12345678916', '{0}'),
('550e8400-e29b-41d4-a716-446655440206', '550e8400-e29b-41d4-a716-446655440002', 'Celtas', 'Capitán Celtas', 'capitan.celtas@example.com', '+12345678917', '{0}'),
('550e8400-e29b-41d4-a716-446655440207', '550e8400-e29b-41d4-a716-446655440002', 'Gators', 'Capitán Gators', 'capitan.gators@example.com', '+12345678918', '{0}'),
('550e8400-e29b-41d4-a716-446655440208', '550e8400-e29b-41d4-a716-446655440002', 'Organizacion UBS', 'Capitán Organizacion UBS', 'capitan.organizacionubs@example.com', '+12345678919', '{0}'),
('550e8400-e29b-41d4-a716-446655440209', '550e8400-e29b-41d4-a716-446655440002', 'Rinos', 'Capitán Rinos', 'capitan.rinos@example.com', '+12345678920', '{0}'),
('550e8400-e29b-41d4-a716-446655440210', '550e8400-e29b-41d4-a716-446655440002', 'Genuinos', 'Capitán Genuinos', 'capitan.genuinos@example.com', '+12345678921', '{0}'),
('550e8400-e29b-41d4-a716-446655440211', '550e8400-e29b-41d4-a716-446655440002', 'Claret', 'Capitán Claret', 'capitan.claret@example.com', '+12345678922', '{0}');

-- Maxi 50 Femenino Teams (15 teams)
INSERT INTO teams (id, tournament_id, name, captain_name, captain_email, captain_phone, preferred_days) VALUES
('550e8400-e29b-41d4-a716-446655440300', '550e8400-e29b-41d4-a716-446655440003', 'Jamals', 'Capitán Jamals', 'capitan.jamals@example.com', '+12345678923', '{0}'),
('550e8400-e29b-41d4-a716-446655440301', '550e8400-e29b-41d4-a716-446655440003', 'Fusion', 'Capitán Fusion', 'capitan.fusion@example.com', '+12345678924', '{0}'),
('550e8400-e29b-41d4-a716-446655440302', '550e8400-e29b-41d4-a716-446655440003', 'Friends', 'Capitán Friends', 'capitan.friends@example.com', '+12345678925', '{0}'),
('550e8400-e29b-41d4-a716-446655440303', '550e8400-e29b-41d4-a716-446655440003', 'UBS', 'Capitán UBS', 'capitan.ubs@example.com', '+12345678926', '{0}'),
('550e8400-e29b-41d4-a716-446655440304', '550e8400-e29b-41d4-a716-446655440003', 'Yacks', 'Capitán Yacks', 'capitan.yacks@example.com', '+12345678927', '{0}'),
('550e8400-e29b-41d4-a716-446655440305', '550e8400-e29b-41d4-a716-446655440003', 'Danals', 'Capitán Danals', 'capitan.danals@example.com', '+12345678928', '{0}'),
('550e8400-e29b-41d4-a716-446655440306', '550e8400-e29b-41d4-a716-446655440003', 'Charlotte', 'Capitán Charlotte', 'capitan.charlotte@example.com', '+12345678929', '{0}'),
('550e8400-e29b-41d4-a716-446655440307', '550e8400-e29b-41d4-a716-446655440003', 'Five', 'Capitán Five', 'capitan.five@example.com', '+12345678930', '{0}'),
('550e8400-e29b-41d4-a716-446655440308', '550e8400-e29b-41d4-a716-446655440003', 'Quinciañeras', 'Capitán Quinciañeras', 'capitan.quincaneras@example.com', '+12345678931', '{0}'),
('550e8400-e29b-41d4-a716-446655440309', '550e8400-e29b-41d4-a716-446655440003', 'Rolas', 'Capitán Rolas', 'capitan.rolas@example.com', '+12345678932', '{0}'),
('550e8400-e29b-41d4-a716-446655440310', '550e8400-e29b-41d4-a716-446655440003', 'Caneo', 'Capitán Caneo', 'capitan.caneo@example.com', '+12345678933', '{0}'),
('550e8400-e29b-41d4-a716-446655440311', '550e8400-e29b-41d4-a716-446655440003', 'Divisy', 'Capitán Divisy', 'capitan.divisy@example.com', '+12345678934', '{0}'),
('550e8400-e29b-41d4-a716-446655440312', '550e8400-e29b-41d4-a716-446655440003', 'Flanegor', 'Capitán Flanegor', 'capitan.flanegor@example.com', '+12345678935', '{0}'),
('550e8400-e29b-41d4-a716-446655440313', '550e8400-e29b-41d4-a716-446655440003', 'Independiente', 'Capitán Independiente', 'capitan.independiente@example.com', '+12345678936', '{0}'),
('550e8400-e29b-41d4-a716-446655440314', '550e8400-e29b-41d4-a716-446655440003', 'Eskennbal', 'Capitán Eskennbal', 'capitan.eskennbal@example.com', '+12345678937', '{0}');
