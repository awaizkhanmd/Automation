"""
SQLAlchemy database models for job automation system.

This module defines all database tables and relationships using
SQLAlchemy ORM with proper constraints and indexing.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, 
    ForeignKey, Enum, JSON, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum


Base = declarative_base()


class ApplicationStatus(PyEnum):
    """Application status enumeration."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FAILED = "failed"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"
    INTERVIEW = "interview"
    OFFER = "offer"


class SessionStatus(PyEnum):
    """Automation session status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class UserProfile(Base):
    """
    User profile model for storing user information and preferences.
    
    This model stores all user-specific data including personal information,
    preferences, and configuration settings for job applications.
    """
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_name = Column(String(100), nullable=False, unique=True)
    
    # Personal Information
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20))
    location = Column(String(255))
    
    # Professional Information
    current_title = Column(String(255))
    target_roles = Column(JSON)  # List of target job titles
    skills = Column(JSON)  # List of skills/technologies
    experience_years = Column(Integer)
    
    # Job Search Preferences
    preferred_locations = Column(JSON)  # List of preferred work locations
    remote_preference = Column(String(20))  # remote, hybrid, onsite, any
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    job_types = Column(JSON)  # full_time, contract, part_time, etc.
    
    # Site-specific credentials (encrypted in production)
    linkedin_email = Column(String(255))
    linkedin_password = Column(String(255))  # Should be encrypted
    indeed_email = Column(String(255))
    indeed_password = Column(String(255))  # Should be encrypted
    dice_email = Column(String(255))
    dice_password = Column(String(255))  # Should be encrypted
    
    # Configuration
    max_applications_per_day = Column(Integer, default=50)
    application_delay_seconds = Column(Integer, default=3)
    preferred_sites = Column(JSON)  # List of preferred job sites
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job_applications = relationship("JobApplication", back_populates="user_profile")
    automation_sessions = relationship("AutomationSession", back_populates="user_profile")
    
    def __repr__(self):
        return f"<UserProfile(id={self.id}, name='{self.profile_name}')>"


class JobPosting(Base):
    """
    Job posting model for storing job details and requirements.
    
    This model stores information about job postings from various sites
    to avoid duplicate applications and track job details.
    """
    __tablename__ = "job_postings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Job Identification
    external_id = Column(String(255))  # Job ID from the job site
    job_site = Column(String(50), nullable=False)  # linkedin, indeed, dice
    job_url = Column(Text, nullable=False)
    
    # Job Details
    title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    location = Column(String(255))
    job_type = Column(String(50))  # full_time, contract, etc.
    experience_level = Column(String(50))
    
    # Job Description and Requirements
    description = Column(Text)
    requirements = Column(Text)
    salary_range = Column(String(100))
    benefits = Column(Text)
    
    # Posting Metadata
    posted_date = Column(DateTime)
    application_deadline = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # System Metadata
    discovered_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job_applications = relationship("JobApplication", back_populates="job_posting")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_job_posting_site_external_id", "job_site", "external_id"),
        Index("idx_job_posting_company", "company_name"),
        Index("idx_job_posting_location", "location"),
        Index("idx_job_posting_posted_date", "posted_date"),
        UniqueConstraint("job_site", "external_id", name="uq_job_site_external_id"),
    )
    
    def __repr__(self):
        return f"<JobPosting(id={self.id}, title='{self.title}', company='{self.company_name}')>"


class JobApplication(Base):
    """
    Job application model for tracking application attempts and results.
    
    This model tracks each job application attempt including status,
    timestamps, and any errors or notes from the application process.
    """
    __tablename__ = "job_applications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("automation_sessions.id"))
    
    # Application Details
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING)
    application_date = Column(DateTime, default=datetime.utcnow)
    
    # Resume and Cover Letter Used
    resume_path = Column(String(500))
    cover_letter_path = Column(String(500))
    custom_resume_keywords = Column(JSON)  # Keywords added for this application
    
    # Application Response Tracking
    response_received = Column(Boolean, default=False)
    response_date = Column(DateTime)
    response_type = Column(String(50))  # rejection, interview_request, etc.
    response_notes = Column(Text)
    
    # Interview Tracking
    interview_scheduled = Column(Boolean, default=False)
    interview_date = Column(DateTime)
    interview_type = Column(String(50))  # phone, video, in_person
    interview_notes = Column(Text)
    
    # Outcome Tracking
    offer_received = Column(Boolean, default=False)
    offer_date = Column(DateTime)
    offer_amount = Column(Integer)
    offer_accepted = Column(Boolean)
    
    # Error and Debug Information
    error_message = Column(Text)
    screenshot_path = Column(String(500))
    form_data_used = Column(JSON)  # Data that was filled in forms
    
    # Metadata
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_profile = relationship("UserProfile", back_populates="job_applications")
    job_posting = relationship("JobPosting", back_populates="job_applications")
    automation_session = relationship("AutomationSession", back_populates="job_applications")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_job_application_user_profile", "user_profile_id"),
        Index("idx_job_application_status", "status"),
        Index("idx_job_application_date", "application_date"),
        Index("idx_job_application_session", "session_id"),
        UniqueConstraint("user_profile_id", "job_posting_id", name="uq_user_job_application"),
    )
    
    def __repr__(self):
        return f"<JobApplication(id={self.id}, status='{self.status.value}')>"


class AutomationSession(Base):
    """
    Automation session model for tracking automation runs and statistics.
    
    This model tracks each automation session including start/end times,
    success rates, and session-specific configuration.
    """
    __tablename__ = "automation_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    
    # Session Details
    session_name = Column(String(255))
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)
    
    # Timing Information
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # Session Configuration
    target_sites = Column(JSON)  # List of job sites to target
    max_applications_target = Column(Integer)
    search_keywords = Column(JSON)
    search_locations = Column(JSON)
    
    # Session Statistics
    applications_attempted = Column(Integer, default=0)
    applications_successful = Column(Integer, default=0)
    applications_failed = Column(Integer, default=0)
    applications_duplicate = Column(Integer, default=0)
    
    # Site-specific Statistics
    linkedin_applications = Column(Integer, default=0)
    indeed_applications = Column(Integer, default=0)
    dice_applications = Column(Integer, default=0)
    
    # Performance Metrics
    average_application_time = Column(Integer)  # Seconds per application
    success_rate = Column(Integer)  # Percentage
    
    # Error Tracking
    total_errors = Column(Integer, default=0)
    critical_errors = Column(Integer, default=0)
    
    # Session Notes and Configuration
    session_notes = Column(Text)
    browser_config = Column(JSON)
    automation_config = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_profile = relationship("UserProfile", back_populates="automation_sessions")
    job_applications = relationship("JobApplication", back_populates="automation_session")
    error_logs = relationship("ErrorLog", back_populates="automation_session")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_automation_session_user_profile", "user_profile_id"),
        Index("idx_automation_session_status", "status"),
        Index("idx_automation_session_started_at", "started_at"),
    )
    
    def __repr__(self):
        return f"<AutomationSession(id={self.id}, status='{self.status.value}')>"


class ErrorLog(Base):
    """
    Error log model for comprehensive error tracking and debugging.
    
    This model stores detailed error information to help with debugging
    and improving the automation system.
    """
    __tablename__ = "error_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    session_id = Column(Integer, ForeignKey("automation_sessions.id"))
    job_application_id = Column(Integer, ForeignKey("job_applications.id"))
    
    # Error Classification
    error_type = Column(String(100), nullable=False)  # browser, form, network, etc.
    error_category = Column(String(50))  # critical, warning, info
    job_site = Column(String(50))  # Site where error occurred
    
    # Error Details
    error_message = Column(Text, nullable=False)
    error_stack_trace = Column(Text)
    error_code = Column(String(50))
    
    # Context Information
    url_at_error = Column(Text)
    page_title = Column(String(255))
    form_data_attempted = Column(JSON)
    browser_state = Column(JSON)
    
    # Recovery Information
    recovery_attempted = Column(Boolean, default=False)
    recovery_successful = Column(Boolean, default=False)
    recovery_method = Column(String(100))
    
    # Supporting Files
    screenshot_path = Column(String(500))
    page_source_path = Column(String(500))
    log_file_path = Column(String(500))
    
    # Metadata
    occurred_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    
    # Relationships
    automation_session = relationship("AutomationSession", back_populates="error_logs")
    job_application = relationship("JobApplication")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_error_log_session", "session_id"),
        Index("idx_error_log_type", "error_type"),
        Index("idx_error_log_occurred_at", "occurred_at"),
        Index("idx_error_log_job_site", "job_site"),
    )
    
    def __repr__(self):
        return f"<ErrorLog(id={self.id}, type='{self.error_type}')>""""
SQLAlchemy database models for job automation system.

This module defines all database tables and relationships using
SQLAlchemy ORM with proper constraints and indexing.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, 
    ForeignKey, Enum, JSON, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum


Base = declarative_base()


class ApplicationStatus(PyEnum):
    """Application status enumeration."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FAILED = "failed"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"
    INTERVIEW = "interview"
    OFFER = "offer"


class SessionStatus(PyEnum):
    """Automation session status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class UserProfile(Base):
    """
    User profile model for storing user information and preferences.
    
    This model stores all user-specific data including personal information,
    preferences, and configuration settings for job applications.
    """
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_name = Column(String(100), nullable=False, unique=True)
    
    # Personal Information
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20))
    location = Column(String(255))
    
    # Professional Information
    current_title = Column(String(255))
    target_roles = Column(JSON)  # List of target job titles
    skills = Column(JSON)  # List of skills/technologies
    experience_years = Column(Integer)
    
    # Job Search Preferences
    preferred_locations = Column(JSON)  # List of preferred work locations
    remote_preference = Column(String(20))  # remote, hybrid, onsite, any
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    job_types = Column(JSON)  # full_time, contract, part_time, etc.
    
    # Site-specific credentials (encrypted in production)
    linkedin_email = Column(String(255))
    linkedin_password = Column(String(255))  # Should be encrypted
    indeed_email = Column(String(255))
    indeed_password = Column(String(255))  # Should be encrypted
    dice_email = Column(String(255))
    dice_password = Column(String(255))  # Should be encrypted
    
    # Configuration
    max_applications_per_day = Column(Integer, default=50)
    application_delay_seconds = Column(Integer, default=3)
    preferred_sites = Column(JSON)  # List of preferred job sites
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job_applications = relationship("JobApplication", back_populates="user_profile")
    automation_sessions = relationship("AutomationSession", back_populates="user_profile")
    
    def __repr__(self):
        return f"<UserProfile(id={self.id}, name='{self.profile_name}')>"


class JobPosting(Base):
    """
    Job posting model for storing job details and requirements.
    
    This model stores information about job postings from various sites
    to avoid duplicate applications and track job details.
    """
    __tablename__ = "job_postings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Job Identification
    external_id = Column(String(255))  # Job ID from the job site
    job_site = Column(String(50), nullable=False)  # linkedin, indeed, dice
    job_url = Column(Text, nullable=False)
    
    # Job Details
    title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    location = Column(String(255))
    job_type = Column(String(50))  # full_time, contract, etc.
    experience_level = Column(String(50))
    
    # Job Description and Requirements
    description = Column(Text)
    requirements = Column(Text)
    salary_range = Column(String(100))
    benefits = Column(Text)
    
    # Posting Metadata
    posted_date = Column(DateTime)
    application_deadline = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # System Metadata
    discovered_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job_applications = relationship("JobApplication", back_populates="job_posting")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_job_posting_site_external_id", "job_site", "external_id"),
        Index("idx_job_posting_company", "company_name"),
        Index("idx_job_posting_location", "location"),
        Index("idx_job_posting_posted_date", "posted_date"),
        UniqueConstraint("job_site", "external_id", name="uq_job_site_external_id"),
    )
    
    def __repr__(self):
        return f"<JobPosting(id={self.id}, title='{self.title}', company='{self.company_name}')>"


class JobApplication(Base):
    """
    Job application model for tracking application attempts and results.
    
    This model tracks each job application attempt including status,
    timestamps, and any errors or notes from the application process.
    """
    __tablename__ = "job_applications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("automation_sessions.id"))
    
    # Application Details
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING)
    application_date = Column(DateTime, default=datetime.utcnow)
    
    # Resume and Cover Letter Used
    resume_path = Column(String(500))
    cover_letter_path = Column(String(500))
    custom_resume_keywords = Column(JSON)  # Keywords added for this application
    
    # Application Response Tracking
    response_received = Column(Boolean, default=False)
    response_date = Column(DateTime)
    response_type = Column(String(50))  # rejection, interview_request, etc.
    response_notes = Column(Text)
    
    # Interview Tracking
    interview_scheduled = Column(Boolean, default=False)
    interview_date = Column(DateTime)
    interview_type = Column(String(50))  # phone, video, in_person
    interview_notes = Column(Text)
    
    # Outcome Tracking
    offer_received = Column(Boolean, default=False)
    offer_date = Column(DateTime)
    offer_amount = Column(Integer)
    offer_accepted = Column(Boolean)
    
    # Error and Debug Information
    error_message = Column(Text)
    screenshot_path = Column(String(500))
    form_data_used = Column(JSON)  # Data that was filled in forms
    
    # Metadata
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_profile = relationship("UserProfile", back_populates="job_applications")
    job_posting = relationship("JobPosting", back_populates="job_applications")
    automation_session = relationship("AutomationSession", back_populates="job_applications")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_job_application_user_profile", "user_profile_id"),
        Index("idx_job_application_status", "status"),
        Index("idx_job_application_date", "application_date"),
        Index("idx_job_application_session", "session_id"),
        UniqueConstraint("user_profile_id", "job_posting_id", name="uq_user_job_application"),
    )
    
    def __repr__(self):
        return f"<JobApplication(id={self.id}, status='{self.status.value}')>"


class AutomationSession(Base):
    """
    Automation session model for tracking automation runs and statistics.
    
    This model tracks each automation session including start/end times,
    success rates, and session-specific configuration.
    """
    __tablename__ = "automation_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    
    # Session Details
    session_name = Column(String(255))
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)
    
    # Timing Information
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # Session Configuration
    target_sites = Column(JSON)  # List of job sites to target
    max_applications_target = Column(Integer)
    search_keywords = Column(JSON)
    search_locations = Column(JSON)
    
    # Session Statistics
    applications_attempted = Column(Integer, default=0)
    applications_successful = Column(Integer, default=0)
    applications_failed = Column(Integer, default=0)
    applications_duplicate = Column(Integer, default=0)
    
    # Site-specific Statistics
    linkedin_applications = Column(Integer, default=0)
    indeed_applications = Column(Integer, default=0)
    dice_applications = Column(Integer, default=0)
    
    # Performance Metrics
    average_application_time = Column(Integer)  # Seconds per application
    success_rate = Column(Integer)  # Percentage
    
    # Error Tracking
    total_errors = Column(Integer, default=0)
    critical_errors = Column(Integer, default=0)
    
    # Session Notes and Configuration
    session_notes = Column(Text)
    browser_config = Column(JSON)
    automation_config = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_profile = relationship("UserProfile", back_populates="automation_sessions")
    job_applications = relationship("JobApplication", back_populates="automation_session")
    error_logs = relationship("ErrorLog", back_populates="automation_session")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_automation_session_user_profile", "user_profile_id"),
        Index("idx_automation_session_status", "status"),
        Index("idx_automation_session_started_at", "started_at"),
    )
    
    def __repr__(self):
        return f"<AutomationSession(id={self.id}, status='{self.status.value}')>"


class ErrorLog(Base):
    """
    Error log model for comprehensive error tracking and debugging.
    
    This model stores detailed error information to help with debugging
    and improving the automation system.
    """
    __tablename__ = "error_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    session_id = Column(Integer, ForeignKey("automation_sessions.id"))
    job_application_id = Column(Integer, ForeignKey("job_applications.id"))
    
    # Error Classification
    error_type = Column(String(100), nullable=False)  # browser, form, network, etc.
    error_category = Column(String(50))  # critical, warning, info
    job_site = Column(String(50))  # Site where error occurred
    
    # Error Details
    error_message = Column(Text, nullable=False)
    error_stack_trace = Column(Text)
    error_code = Column(String(50))
    
    # Context Information
    url_at_error = Column(Text)
    page_title = Column(String(255))
    form_data_attempted = Column(JSON)
    browser_state = Column(JSON)
    
    # Recovery Information
    recovery_attempted = Column(Boolean, default=False)
    recovery_successful = Column(Boolean, default=False)
    recovery_method = Column(String(100))
    
    # Supporting Files
    screenshot_path = Column(String(500))
    page_source_path = Column(String(500))
    log_file_path = Column(String(500))
    
    # Metadata
    occurred_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    
    # Relationships
    automation_session = relationship("AutomationSession", back_populates="error_logs")
    job_application = relationship("JobApplication")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_error_log_session", "session_id"),
        Index("idx_error_log_type", "error_type"),
        Index("idx_error_log_occurred_at", "occurred_at"),
        Index("idx_error_log_job_site", "job_site"),
    )
    
    def __repr__(self):
        return f"<ErrorLog(id={self.id}, type='{self.error_type}')>"