_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """
    Get global database manager instance.
    
    Returns:
        DatabaseManager: Database manager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db_session() -> Session:
    """
    Get a new database session.
    
    Returns:
        Session: SQLAlchemy session
    """
    return get_database_manager().get_session()


@contextmanager
def db_session_scope() -> Generator[Session, None, None]:
    """
    Context manager for database session with automatic transaction handling.
    
    Yields:
        Session: Database session
    """
    with get_database_manager().session_scope() as session:
        yield session
```

### database/migrations/001_initial_schema.sql
```sql
-- Initial database schema for job automation system
-- This file contains the complete database schema creation

-- Enable UUID extension (optional, for future use)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create ENUM types
CREATE TYPE application_status AS ENUM (
    'pending', 'submitted', 'failed', 'duplicate', 
    'rejected', 'interview', 'offer'
);

CREATE TYPE session_status AS ENUM (
    'active', 'completed', 'failed', 'cancelled'
);

-- User Profiles Table
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    profile_name VARCHAR(100) NOT NULL UNIQUE,
    
    -- Personal Information
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    location VARCHAR(255),
    
    -- Professional Information
    current_title VARCHAR(255),
    target_roles JSONB,
    skills JSONB,
    experience_years INTEGER,
    
    -- Job Search Preferences
    preferred_locations JSONB,
    remote_preference VARCHAR(20),
    salary_min INTEGER,
    salary_max INTEGER,
    job_types JSONB,
    
    -- Site-specific credentials (should be encrypted in production)
    linkedin_email VARCHAR(255),
    linkedin_password VARCHAR(255),
    indeed_email VARCHAR(255),
    indeed_password VARCHAR(255),
    dice_email VARCHAR(255),
    dice_password VARCHAR(255),
    
    -- Configuration
    max_applications_per_day INTEGER DEFAULT 50,
    application_delay_seconds INTEGER DEFAULT 3,
    preferred_sites JSONB,
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job Postings Table
CREATE TABLE job_postings (
    id SERIAL PRIMARY KEY,
    
    -- Job Identification
    external_id VARCHAR(255),
    job_site VARCHAR(50) NOT NULL,
    job_url TEXT NOT NULL,
    
    -- Job Details
    title VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    job_type VARCHAR(50),
    experience_level VARCHAR(50),
    
    -- Job Description and Requirements
    description TEXT,
    requirements TEXT,
    salary_range VARCHAR(100),
    benefits TEXT,
    
    -- Posting Metadata
    posted_date TIMESTAMP,
    application_deadline TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- System Metadata
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint to prevent duplicate job postings
    CONSTRAINT uq_job_site_external_id UNIQUE (job_site, external_id)
);

-- Automation Sessions Table
CREATE TABLE automation_sessions (
    id SERIAL PRIMARY KEY,
    user_profile_id INTEGER NOT NULL REFERENCES user_profiles(id),
    
    -- Session Details
    session_name VARCHAR(255),
    status session_status DEFAULT 'active',
    
    -- Timing Information
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    
    -- Session Configuration
    target_sites JSONB,
    max_applications_target INTEGER,
    search_keywords JSONB,
    search_locations JSONB,
    
    -- Session Statistics
    applications_attempted INTEGER DEFAULT 0,
    applications_successful INTEGER DEFAULT 0,
    applications_failed INTEGER DEFAULT 0,
    applications_duplicate INTEGER DEFAULT 0,
    
    -- Site-specific Statistics
    linkedin_applications INTEGER DEFAULT 0,
    indeed_applications INTEGER DEFAULT 0,
    dice_applications INTEGER DEFAULT 0,
    
    -- Performance Metrics
    average_application_time INTEGER,
    success_rate INTEGER,
    
    -- Error Tracking
    total_errors INTEGER DEFAULT 0,
    critical_errors INTEGER DEFAULT 0,
    
    -- Session Notes and Configuration
    session_notes TEXT,
    browser_config JSONB,
    automation_config JSONB,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job Applications Table
CREATE TABLE job_applications (
    id SERIAL PRIMARY KEY,
    user_profile_id INTEGER NOT NULL REFERENCES user_profiles(id),
    job_posting_id INTEGER NOT NULL REFERENCES job_postings(id),
    session_id INTEGER REFERENCES automation_sessions(id),
    
    -- Application Details
    status application_status DEFAULT 'pending',
    application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Resume and Cover Letter Used
    resume_path VARCHAR(500),
    cover_letter_path VARCHAR(500),
    custom_resume_keywords JSONB,
    
    -- Application Response Tracking
    response_received BOOLEAN DEFAULT FALSE,
    response_date TIMESTAMP,
    response_type VARCHAR(50),
    response_notes TEXT,
    
    -- Interview Tracking
    interview_scheduled BOOLEAN DEFAULT FALSE,
    interview_date TIMESTAMP,
    interview_type VARCHAR(50),
    interview_notes TEXT,
    
    -- Outcome Tracking
    offer_received BOOLEAN DEFAULT FALSE,
    offer_date TIMESTAMP,
    offer_amount INTEGER,
    offer_accepted BOOLEAN,
    
    -- Error and Debug Information
    error_message TEXT,
    screenshot_path VARCHAR(500),
    form_data_used JSONB,
    
    -- Metadata
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint to prevent duplicate applications
    CONSTRAINT uq_user_job_application UNIQUE (user_profile_id, job_posting_id)
);

-- Error Logs Table
CREATE TABLE error_logs (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES automation_sessions(id),
    job_application_id INTEGER REFERENCES job_applications(id),
    
    -- Error Classification
    error_type VARCHAR(100) NOT NULL,
    error_category VARCHAR(50),
    job_site VARCHAR(50),
    
    -- Error Details
    error_message TEXT NOT NULL,
    error_stack_trace TEXT,
    error_code VARCHAR(50),
    
    -- Context Information
    url_at_error TEXT,
    page_title VARCHAR(255),
    form_data_attempted JSONB,
    browser_state JSONB,
    
    -- Recovery Information
    recovery_attempted BOOLEAN DEFAULT FALSE,
    recovery_successful BOOLEAN DEFAULT FALSE,
    recovery_method VARCHAR(100),
    
    -- Supporting Files
    screenshot_path VARCHAR(500),
    page_source_path VARCHAR(500),
    log_file_path VARCHAR(500),
    
    -- Metadata
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution_notes TEXT
);

-- Create Indexes for Performance
CREATE INDEX idx_job_posting_site_external_id ON job_postings(job_site, external_id);
CREATE INDEX idx_job_posting_company ON job_postings(company_name);
CREATE INDEX idx_job_posting_location ON job_postings(location);
CREATE INDEX idx_job_posting_posted_date ON job_postings(posted_date);

CREATE INDEX idx_job_application_user_profile ON job_applications(user_profile_id);
CREATE INDEX idx_job_application_status ON job_applications(status);
CREATE INDEX idx_job_application_date ON job_applications(application_date);
CREATE INDEX idx_job_application_session ON job_applications(session_id);

CREATE INDEX idx_automation_session_user_profile ON automation_sessions(user_profile_id);
CREATE INDEX idx_automation_session_status ON automation_sessions(status);
CREATE INDEX idx_automation_session_started_at ON automation_sessions(started_at);

CREATE INDEX idx_error_log_session ON error_logs(session_id);
CREATE INDEX idx_error_log_type ON error_logs(error_type);
CREATE INDEX idx_error_log_occurred_at ON error_logs(occurred_at);
CREATE INDEX idx_error_log_job_site ON error_logs(job_site);

-- Create a trigger to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply the trigger to tables with updated_at columns
CREATE TRIGGER update_user_profiles_updated_at 
    BEFORE UPDATE ON user_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_job_postings_updated_at 
    BEFORE UPDATE ON job_postings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_automation_sessions_updated_at 
    BEFORE UPDATE ON automation_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_job_applications_updated_at 
    BEFORE UPDATE ON job_applications 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default user profile (optional)
INSERT INTO user_profiles (
    profile_name, first_name, last_name, email,
    target_roles, skills, preferred_locations, job_types, preferred_sites
) VALUES (
    'default_profile',
    'Job', 'Seeker', 'jobseeker@example.com',
    '["Software Engineer", "Python Developer", "Full Stack Developer"]'::jsonb,
    '["Python", "JavaScript", "SQL", "React", "Django"]'::jsonb,
    '["Remote", "San Francisco", "New York", "Austin"]'::jsonb,
    '["full_time", "contract"]'::jsonb,
    '["linkedin", "indeed", "dice"]'::jsonb
);

-- Show table creation summary
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN ('user_profiles', 'job_postings', 'job_applications', 'automation_sessions', 'error_logs')
ORDER BY tablename;_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """
    Get global database manager instance.
    
    Returns:
        DatabaseManager: Database manager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db_session() -> Session:
    """
    Get a new database session.
    
    Returns:
        Session: SQLAlchemy session
    """
    return get_database_manager().get_session()


@contextmanager
def db_session_scope() -> Generator[Session, None, None]:
    """
    Context manager for database session with automatic transaction handling.
    
    Yields:
        Session: Database session
    """
    with get_database_manager().session_scope() as session:
        yield session
```

### database/migrations/001_initial_schema.sql
```sql
-- Initial database schema for job automation system
-- This file contains the complete database schema creation

-- Enable UUID extension (optional, for future use)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create ENUM types
CREATE TYPE application_status AS ENUM (
    'pending', 'submitted', 'failed', 'duplicate', 
    'rejected', 'interview', 'offer'
);

CREATE TYPE session_status AS ENUM (
    'active', 'completed', 'failed', 'cancelled'
);

-- User Profiles Table
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    profile_name VARCHAR(100) NOT NULL UNIQUE,
    
    -- Personal Information
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    location VARCHAR(255),
    
    -- Professional Information
    current_title VARCHAR(255),
    target_roles JSONB,
    skills JSONB,
    experience_years INTEGER,
    
    -- Job Search Preferences
    preferred_locations JSONB,
    remote_preference VARCHAR(20),
    salary_min INTEGER,
    salary_max INTEGER,
    job_types JSONB,
    
    -- Site-specific credentials (should be encrypted in production)
    linkedin_email VARCHAR(255),
    linkedin_password VARCHAR(255),
    indeed_email VARCHAR(255),
    indeed_password VARCHAR(255),
    dice_email VARCHAR(255),
    dice_password VARCHAR(255),
    
    -- Configuration
    max_applications_per_day INTEGER DEFAULT 50,
    application_delay_seconds INTEGER DEFAULT 3,
    preferred_sites JSONB,
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job Postings Table
CREATE TABLE job_postings (
    id SERIAL PRIMARY KEY,
    
    -- Job Identification
    external_id VARCHAR(255),
    job_site VARCHAR(50) NOT NULL,
    job_url TEXT NOT NULL,
    
    -- Job Details
    title VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    job_type VARCHAR(50),
    experience_level VARCHAR(50),
    
    -- Job Description and Requirements
    description TEXT,
    requirements TEXT,
    salary_range VARCHAR(100),
    benefits TEXT,
    
    -- Posting Metadata
    posted_date TIMESTAMP,
    application_deadline TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- System Metadata
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint to prevent duplicate job postings
    CONSTRAINT uq_job_site_external_id UNIQUE (job_site, external_id)
);

-- Automation Sessions Table
CREATE TABLE automation_sessions (
    id SERIAL PRIMARY KEY,
    user_profile_id INTEGER NOT NULL REFERENCES user_profiles(id),
    
    -- Session Details
    session_name VARCHAR(255),
    status session_status DEFAULT 'active',
    
    -- Timing Information
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    
    -- Session Configuration
    target_sites JSONB,
    max_applications_target INTEGER,
    search_keywords JSONB,
    search_locations JSONB,
    
    -- Session Statistics
    applications_attempted INTEGER DEFAULT 0,
    applications_successful INTEGER DEFAULT 0,
    applications_failed INTEGER DEFAULT 0,
    applications_duplicate INTEGER DEFAULT 0,
    
    -- Site-specific Statistics
    linkedin_applications INTEGER DEFAULT 0,
    indeed_applications INTEGER DEFAULT 0,
    dice_applications INTEGER DEFAULT 0,
    
    -- Performance Metrics
    average_application_time INTEGER,
    success_rate INTEGER,
    
    -- Error Tracking
    total_errors INTEGER DEFAULT 0,
    critical_errors INTEGER DEFAULT 0,
    
    -- Session Notes and Configuration
    session_notes TEXT,
    browser_config JSONB,
    automation_config JSONB,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job Applications Table
CREATE TABLE job_applications (
    id SERIAL PRIMARY KEY,
    user_profile_id INTEGER NOT NULL REFERENCES user_profiles(id),
    job_posting_id INTEGER NOT NULL REFERENCES job_postings(id),
    session_id INTEGER REFERENCES automation_sessions(id),
    
    -- Application Details
    status application_status DEFAULT 'pending',
    application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Resume and Cover Letter Used
    resume_path VARCHAR(500),
    cover_letter_path VARCHAR(500),
    custom_resume_keywords JSONB,
    
    -- Application Response Tracking
    response_received BOOLEAN DEFAULT FALSE,
    response_date TIMESTAMP,
    response_type VARCHAR(50),
    response_notes TEXT,
    
    -- Interview Tracking
    interview_scheduled BOOLEAN DEFAULT FALSE,
    interview_date TIMESTAMP,
    interview_type VARCHAR(50),
    interview_notes TEXT,
    
    -- Outcome Tracking
    offer_received BOOLEAN DEFAULT FALSE,
    offer_date TIMESTAMP,
    offer_amount INTEGER,
    offer_accepted BOOLEAN,
    
    -- Error and Debug Information
    error_message TEXT,
    screenshot_path VARCHAR(500),
    form_data_used JSONB,
    
    -- Metadata
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint to prevent duplicate applications
    CONSTRAINT uq_user_job_application UNIQUE (user_profile_id, job_posting_id)
);

-- Error Logs Table
CREATE TABLE error_logs (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES automation_sessions(id),
    job_application_id INTEGER REFERENCES job_applications(id),
    
    -- Error Classification
    error_type VARCHAR(100) NOT NULL,
    error_category VARCHAR(50),
    job_site VARCHAR(50),
    
    -- Error Details
    error_message TEXT NOT NULL,
    error_stack_trace TEXT,
    error_code VARCHAR(50),
    
    -- Context Information
    url_at_error TEXT,
    page_title VARCHAR(255),
    form_data_attempted JSONB,
    browser_state JSONB,
    
    -- Recovery Information
    recovery_attempted BOOLEAN DEFAULT FALSE,
    recovery_successful BOOLEAN DEFAULT FALSE,
    recovery_method VARCHAR(100),
    
    -- Supporting Files
    screenshot_path VARCHAR(500),
    page_source_path VARCHAR(500),
    log_file_path VARCHAR(500),
    
    -- Metadata
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution_notes TEXT
);

-- Create Indexes for Performance
CREATE INDEX idx_job_posting_site_external_id ON job_postings(job_site, external_id);
CREATE INDEX idx_job_posting_company ON job_postings(company_name);
CREATE INDEX idx_job_posting_location ON job_postings(location);
CREATE INDEX idx_job_posting_posted_date ON job_postings(posted_date);

CREATE INDEX idx_job_application_user_profile ON job_applications(user_profile_id);
CREATE INDEX idx_job_application_status ON job_applications(status);
CREATE INDEX idx_job_application_date ON job_applications(application_date);
CREATE INDEX idx_job_application_session ON job_applications(session_id);

CREATE INDEX idx_automation_session_user_profile ON automation_sessions(user_profile_id);
CREATE INDEX idx_automation_session_status ON automation_sessions(status);
CREATE INDEX idx_automation_session_started_at ON automation_sessions(started_at);

CREATE INDEX idx_error_log_session ON error_logs(session_id);
CREATE INDEX idx_error_log_type ON error_logs(error_type);
CREATE INDEX idx_error_log_occurred_at ON error_logs(occurred_at);
CREATE INDEX idx_error_log_job_site ON error_logs(job_site);

-- Create a trigger to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply the trigger to tables with updated_at columns
CREATE TRIGGER update_user_profiles_updated_at 
    BEFORE UPDATE ON user_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_job_postings_updated_at 
    BEFORE UPDATE ON job_postings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_automation_sessions_updated_at 
    BEFORE UPDATE ON automation_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_job_applications_updated_at 
    BEFORE UPDATE ON job_applications 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default user profile (optional)
INSERT INTO user_profiles (
    profile_name, first_name, last_name, email,
    target_roles, skills, preferred_locations, job_types, preferred_sites
) VALUES (
    'default_profile',
    'Job', 'Seeker', 'jobseeker@example.com',
    '["Software Engineer", "Python Developer", "Full Stack Developer"]'::jsonb,
    '["Python", "JavaScript", "SQL", "React", "Django"]'::jsonb,
    '["Remote", "San Francisco", "New York", "Austin"]'::jsonb,
    '["full_time", "contract"]'::jsonb,
    '["linkedin", "indeed", "dice"]'::jsonb
);

-- Show table creation summary
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN ('user_profiles', 'job_postings', 'job_applications', 'automation_sessions', 'error_logs')
ORDER BY tablename;