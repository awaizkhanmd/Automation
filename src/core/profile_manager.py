"""
User profile management system with database persistence.

This module handles user profile creation, validation, loading,
and management with database storage and JSON template support.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from database.models import UserProfile
from database.connection import db_session_scope
from src.utils.helpers import ensure_directory_exists, load_json_file, save_json_file
from src.utils.validators import ProfileValidator, ValidationError

logger = logging.getLogger(__name__)


class ProfileManager:
    """
    User profile manager for handling profile creation, loading, and management.
    
    Manages user profiles with database persistence and JSON template support
    for flexible profile management and application data.
    """
    
    def __init__(self):
        self.profiles_dir = ensure_directory_exists("data/profiles")
        self.validator = ProfileValidator()
    
    def create_profile(self, profile_data: Dict[str, Any]) -> Optional[UserProfile]:
        """
        Create new user profile with validation.
        
        Args:
            profile_data: Profile data dictionary
            
        Returns:
            Created UserProfile or None if creation failed
        """
        try:
            # Validate profile data
            errors = self.validator.validate_profile_data(profile_data)
            if errors:
                error_msg = "Profile validation failed:\n"
                for field, field_errors in errors.items():
                    error_msg += f"  {field}: {', '.join(field_errors)}\n"
                logger.error(error_msg)
                raise ValidationError(error_msg)
            
            # Create profile in database
            with db_session_scope() as session:
                # Check if profile name already exists
                existing = session.query(UserProfile).filter_by(
                    profile_name=profile_data['profile_name']
                ).first()
                
                if existing:
                    logger.error(f"Profile name '{profile_data['profile_name']}' already exists")
                    return None
                
                # Create new profile
                profile = UserProfile(**profile_data)
                session.add(profile)
                session.flush()  # Get the ID
                
                # Save profile template to JSON
                self._save_profile_template(profile)
                
                logger.info(f"Created profile: {profile.profile_name} (ID: {profile.id})")
                return profile
                
        except Exception as e:
            logger.error(f"Error creating profile: {e}")
            return None
    
    def load_profile(self, profile_identifier: str) -> Optional[UserProfile]:
        """
        Load user profile by name or ID.
        
        Args:
            profile_identifier: Profile name or ID
            
        Returns:
            UserProfile or None if not found
        """
        try:
            with db_session_scope() as session:
                # Try to load by ID first (if it's a number)
                if profile_identifier.isdigit():
                    profile = session.query(UserProfile).filter_by(
                        id=int(profile_identifier)
                    ).first()
                else:
                    # Load by profile name
                    profile = session.query(UserProfile).filter_by(
                        profile_name=profile_identifier
                    ).first()
                
                if profile:
                    # Expunge the profile from the session so it can be used outside
                    session.expunge(profile)
                    logger.info(f"Loaded profile: {profile.profile_name}")
                    return profile
                else:
                    logger.warning(f"Profile not found: {profile_identifier}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error loading profile {profile_identifier}: {e}")
            return None
    
    def update_profile(self, profile_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update existing user profile.
        
        Args:
            profile_id: Profile ID to update
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if update successful
        """
        try:
            # Validate updates
            errors = self.validator.validate_profile_data(updates)
            if errors:
                logger.error(f"Profile update validation failed: {errors}")
                return False
            
            with db_session_scope() as session:
                profile = session.query(UserProfile).filter_by(id=profile_id).first()
                
                if not profile:
                    logger.error(f"Profile not found for update: {profile_id}")
                    return False
                
                # Update profile fields
                for field, value in updates.items():
                    if hasattr(profile, field):
                        setattr(profile, field, value)
                
                session.flush()
                
                # Update profile template
                self._save_profile_template(profile)
                
                logger.info(f"Updated profile: {profile.profile_name}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating profile {profile_id}: {e}")
            return False
    
    def delete_profile(self, profile_id: int) -> bool:
        """
        Delete user profile (soft delete by setting inactive).
        
        Args:
            profile_id: Profile ID to delete
            
        Returns:
            bool: True if deletion successful
        """
        try:
            with db_session_scope() as session:
                profile = session.query(UserProfile).filter_by(id=profile_id).first()
                
                if not profile:
                    logger.error(f"Profile not found for deletion: {profile_id}")
                    return False
                
                # Soft delete - set inactive
                profile.is_active = False
                
                logger.info(f"Deleted profile: {profile.profile_name}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting profile {profile_id}: {e}")
            return False
    
    def list_profiles(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        List all user profiles.
        
        Args:
            active_only: Only return active profiles
            
        Returns:
            List of profile summaries
        """
        try:
            with db_session_scope() as session:
                query = session.query(UserProfile)
                
                if active_only:
                    query = query.filter_by(is_active=True)
                
                profiles = query.all()
                
                return [
                    {
                        "id": p.id,
                        "profile_name": p.profile_name,
                        "first_name": p.first_name,
                        "last_name": p.last_name,
                        "email": p.email,
                        "target_roles": p.target_roles,
                        "preferred_sites": p.preferred_sites,
                        "is_active": p.is_active,
                        "created_at": p.created_at.isoformat() if p.created_at else None,
                    }
                    for p in profiles
                ]
                
        except Exception as e:
            logger.error(f"Error listing profiles: {e}")
            return []
    
    def get_profile_for_application(self, profile_id: int) -> Optional[Dict[str, Any]]:
        """
        Get profile data formatted for job applications.
        
        Args:
            profile_id: Profile ID
            
        Returns:
            Profile data dictionary for applications
        """
        profile = self.load_profile(str(profile_id))
        if not profile:
            return None
        
        return {
            # Personal Information
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "full_name": f"{profile.first_name} {profile.last_name}",
            "email": profile.email,
            "phone": profile.phone,
            "location": profile.location,
            
            # Professional Information
            "current_title": profile.current_title,
            "target_roles": profile.target_roles or [],
            "skills": profile.skills or [],
            "experience_years": profile.experience_years,
            
            # Preferences
            "preferred_locations": profile.preferred_locations or [],
            "remote_preference": profile.remote_preference,
            "salary_min": profile.salary_min,
            "salary_max": profile.salary_max,
            "job_types": profile.job_types or [],
            
            # Site Credentials
            "site_credentials": {
                "linkedin": {
                    "email": profile.linkedin_email,
                    "password": profile.linkedin_password,
                },
                "indeed": {
                    "email": profile.indeed_email,
                    "password": profile.indeed_password,
                },
                "dice": {
                    "email": profile.dice_email,
                    "password": profile.dice_password,
                },
            },
            
            # Configuration
            "automation_config": {
                "max_applications_per_day": profile.max_applications_per_day,
                "application_delay_seconds": profile.application_delay_seconds,
                "preferred_sites": profile.preferred_sites or [],
            }
        }
    
    def _save_profile_template(self, profile: UserProfile):
        """
        Save profile as JSON template for backup/export.
        
        Args:
            profile: UserProfile instance
        """
        try:
            template_data = {
                "profile_name": profile.profile_name,
                "personal_info": {
                    "first_name": profile.first_name,
                    "last_name": profile.last_name,
                    "email": profile.email,
                    "phone": profile.phone,
                    "location": profile.location,
                },
                "professional_info": {
                    "current_title": profile.current_title,
                    "target_roles": profile.target_roles,
                    "skills": profile.skills,
                    "experience_years": profile.experience_years,
                },
                "job_preferences": {
                    "preferred_locations": profile.preferred_locations,
                    "remote_preference": profile.remote_preference,
                    "salary_min": profile.salary_min,
                    "salary_max": profile.salary_max,
                    "job_types": profile.job_types,
                },
                "automation_settings": {
                    "max_applications_per_day": profile.max_applications_per_day,
                    "application_delay_seconds": profile.application_delay_seconds,
                    "preferred_sites": profile.preferred_sites,
                },
                "metadata": {
                    "created_at": profile.created_at.isoformat() if profile.created_at else None,
                    "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
                }
            }
            
            template_path = self.profiles_dir / f"{profile.profile_name}_template.json"
            save_json_file(template_data, template_path)
            
        except Exception as e:
            logger.warning(f"Could not save profile template: {e}")
    
    def load_profile_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Load profile from JSON template.
        
        Args:
            template_name: Template filename (without .json)
            
        Returns:
            Profile data dictionary or None
        """
        template_path = self.profiles_dir / f"{template_name}.json"
        return load_json_file(template_path)
    
    def create_profile_from_template(self, template_name: str, new_profile_name: str) -> Optional[UserProfile]:
        """
        Create new profile from existing template.
        
        Args:
            template_name: Template filename (without .json)
            new_profile_name: Name for new profile
            
        Returns:
            Created UserProfile or None
        """
        template_data = self.load_profile_template(template_name)
        if not template_data:
            logger.error(f"Template not found: {template_name}")
            return None
        
        # Flatten template data for profile creation
        profile_data = {
            "profile_name": new_profile_name,
            **template_data.get("personal_info", {}),
            **template_data.get("professional_info", {}),
            **template_data.get("job_preferences", {}),
            **template_data.get("automation_settings", {}),
        }
        
        return self.create_profile(profile_data)
    
    def export_profile(self, profile_id: int, export_path: Optional[str] = None) -> Optional[str]:
        """
        Export profile to JSON file.
        
        Args:
            profile_id: Profile ID to export
            export_path: Optional custom export path
            
        Returns:
            Export file path or None if export failed
        """
        profile = self.load_profile(str(profile_id))
        if not profile:
            return None
        
        try:
            if not export_path:
                export_path = self.profiles_dir / f"export_{profile.profile_name}.json"
            
            export_data = {
                "exported_at": "2025-01-01T00:00:00",  # Current timestamp
                "profile": self.get_profile_for_application(profile_id)
            }
            
            if save_json_file(export_data, export_path):
                logger.info(f"Profile exported to: {export_path}")
                return str(export_path)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error exporting profile: {e}")
            return None
    
    def validate_site_credentials(self, profile: UserProfile, site: str) -> bool:
        """
        Validate that profile has credentials for specific site.
        
        Args:
            profile: UserProfile instance
            site: Site name (linkedin, indeed, dice)
            
        Returns:
            bool: True if credentials are present
        """
        site = site.lower()
        
        if site == "linkedin":
            return bool(profile.linkedin_email and profile.linkedin_password)
        elif site == "indeed":
            return bool(profile.indeed_email and profile.indeed_password)
        elif site == "dice":
            return bool(profile.dice_email and profile.dice_password)
        
        return False
    
    def get_site_credentials(self, profile: UserProfile, site: str) -> Optional[Dict[str, str]]:
        """
        Get site-specific credentials from profile.
        
        Args:
            profile: UserProfile instance
            site: Site name (linkedin, indeed, dice)
            
        Returns:
            Credentials dictionary or None
        """
        if not self.validate_site_credentials(profile, site):
            return None
        
        site = site.lower()
        
        if site == "linkedin":
            return {"email": profile.linkedin_email, "password": profile.linkedin_password}
        elif site == "indeed":
            return {"email": profile.indeed_email, "password": profile.indeed_password}
        elif site == "dice":
            return {"email": profile.dice_email, "password": profile.dice_password}
        
        return None