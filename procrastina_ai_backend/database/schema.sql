-- Database Creation
CREATE DATABASE IF NOT EXISTS procrastina_ai;
USE procrastina_ai;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
  id VARCHAR(36) PRIMARY KEY,
  username VARCHAR(255) NOT NULL,
  mood VARCHAR(50) NOT NULL,
  interests JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Sessions Table
CREATE TABLE IF NOT EXISTS sessions (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  mood VARCHAR(50),
  interests JSON,
  tasks JSON,
  session_started TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  session_ended TIMESTAMP NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX (user_id)
);

-- Tasks Table
CREATE TABLE IF NOT EXISTS tasks (
  id VARCHAR(36) PRIMARY KEY,
  session_id VARCHAR(36) NOT NULL,
  task_name VARCHAR(255) NOT NULL,
  task_category VARCHAR(100),
  estimated_time INT,
  actual_time INT,
  completed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
  INDEX (session_id)
);

-- Disappearances Table (tracks where users went during procrastination)
CREATE TABLE IF NOT EXISTS disappearances (
  id VARCHAR(36) PRIMARY KEY,
  session_id VARCHAR(36) NOT NULL,
  disappearance_type VARCHAR(100) NOT NULL,
  custom_location VARCHAR(255),
  duration_minutes INT,
  ai_response TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
  INDEX (session_id)
);

-- AI Responses Table (stores generated content from OpenAI)
CREATE TABLE IF NOT EXISTS ai_responses (
  id VARCHAR(36) PRIMARY KEY,
  session_id VARCHAR(36) NOT NULL,
  response_type VARCHAR(100) NOT NULL,
  prompt TEXT,
  response_content LONGTEXT,
  tokens_used INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
  INDEX (session_id),
  INDEX (response_type)
);

-- Reports Table
CREATE TABLE IF NOT EXISTS reports (
  id VARCHAR(36) PRIMARY KEY,
  session_id VARCHAR(36) NOT NULL,
  report_date DATE,
  tasks_planned INT,
  tasks_completed INT,
  total_disappearances INT,
  procrastination_score INT,
  ai_summary LONGTEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
  INDEX (session_id),
  UNIQUE KEY unique_report (session_id, report_date)
);

-- Create indexes for common queries
CREATE INDEX idx_sessions_user_created ON sessions(user_id, session_started);
CREATE INDEX idx_disappearances_session_created ON disappearances(session_id, created_at);
CREATE INDEX idx_ai_responses_session_created ON ai_responses(session_id, created_at);
