-- Clean up matches from Saturday tournaments that were incorrectly scheduled for Sunday
-- Only keep matches from the correct Sunday tournaments

-- Delete matches from Saturday tournaments scheduled for Sunday 2025-09-07
DELETE FROM matches 
WHERE scheduled_date = '2025-09-07' 
AND tournament_id IN (
    '8e3cab4c-cf4b-4919-b412-7524525c9ff3', -- Unica Masculino (Saturday tournament)
    '44580393-329a-41cc-abd8-aab7e326aca5', -- Unica Femenino (Saturday tournament)  
    'dce01559-3e2a-4022-9cb7-5792924010cd'  -- Maxi 40 Femenino (Saturday tournament)
);

-- Verify the cleanup
SELECT 
    t.name as tournament_name,
    COUNT(m.id) as match_count
FROM tournaments t
LEFT JOIN matches m ON t.id = m.tournament_id AND m.scheduled_date = '2025-09-07'
GROUP BY t.id, t.name
ORDER BY t.name;
