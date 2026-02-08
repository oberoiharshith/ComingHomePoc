-- Permanent housing rate by program
SELECT
  program_name,
  SUM(exited_flag) AS exits,
  SUM(permanent_housing_flag) AS perm_exits,
  ROUND(1.0 * SUM(permanent_housing_flag) / NULLIF(SUM(exited_flag),0), 3) AS perm_rate
FROM program_engagements
GROUP BY program_name
ORDER BY perm_rate DESC;

-- Missing exit interview rate by provider+program
SELECT
  provider,
  program_name,
  SUM(exited_flag) AS exits,
  SUM(CASE WHEN exit_interview_completed = 0 THEN 1 ELSE 0 END) AS missing_exit_interviews,
  ROUND(1.0 * SUM(CASE WHEN exit_interview_completed = 0 THEN 1 ELSE 0 END) / NULLIF(SUM(exited_flag),0), 3) AS missing_rate
FROM program_engagements
GROUP BY provider, program_name
HAVING exits >= 30
ORDER BY missing_rate DESC;

-- Equity cut: perm housing by race/ethnicity
SELECT
  c.race_ethnicity,
  COUNT(DISTINCT e.client_id) AS exited_clients,
  SUM(e.permanent_housing_flag) AS perm_exits,
  ROUND(1.0 * SUM(e.permanent_housing_flag) / NULLIF(COUNT(DISTINCT e.client_id),0), 3) AS perm_rate
FROM program_engagements e
JOIN clients c ON c.client_id = e.client_id
WHERE e.exited_flag = 1
GROUP BY c.race_ethnicity
ORDER BY perm_rate DESC;
