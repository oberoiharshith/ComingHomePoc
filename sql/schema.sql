DROP TABLE IF EXISTS clients;
DROP TABLE IF EXISTS program_engagements;

CREATE TABLE clients (
  client_id TEXT PRIMARY KEY,
  year INTEGER,
  household_type TEXT,
  age_group TEXT,
  race_ethnicity TEXT,
  gender TEXT,
  primary_program TEXT,
  provider TEXT
);

CREATE TABLE program_engagements (
  client_id TEXT,
  program_name TEXT,
  provider TEXT,
  entry_date TEXT,
  exit_date TEXT,
  exited_flag INTEGER,
  exit_interview_completed INTEGER,
  exit_destination TEXT,
  income_at_exit_range TEXT,
  permanent_housing_flag INTEGER
);