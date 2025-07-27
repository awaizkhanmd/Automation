"""
Database setup and initialization script.

This script creates the database, tables, and initial data
for the job automation system.
"""

import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings
from database.connection import get_database_manager
from database.models import Base, UserProfile
from src.utils.logger import configure_logging

logger = logging.getLogger(__name__)


def create_initial_profile():
    """Create initial user profile with default values."""
    db_manager = get_database_manager()
    
    try:
        with db_manager.session_scope() as session:
            # Check if default profile already exists
            existing_profile = session.query(UserProfile).filter_by(
                profile_name="default_profile"
            ).first()
            
            if existing_profile:
                logger.info("Default profile already exists")
                # Return the profile data, not the object
                return {
                    'id': existing_profile.id,
                    'profile_name': existing_profile.profile_name,
                    'email': existing_profile.email
                }
            
            # Create default profile
            default_profile = UserProfile(
                profile_name="default_profile",
                first_name="Job",
                last_name="Seeker",
                email="jobseeker@example.com",
                current_title="Software Engineer",
                target_roles=["Software Engineer", "Python Developer", "Full Stack Developer"],
                skills=["Python", "JavaScript", "SQL", "React", "Django"],
                experience_years=3,
                preferred_locations=["Remote", "San Francisco", "New York", "Austin"],
                remote_preference="any",
                salary_min=80000,
                salary_max=120000,
                job_types=["full_time", "contract"],
                preferred_sites=["linkedin", "indeed", "dice"],
                max_applications_per_day=50,
                application_delay_seconds=3,
            )
            
            session.add(default_profile)
            session.commit()
            
            # Get the ID and other info before session ends
            profile_data = {
                'id': default_profile.id,
                'profile_name': default_profile.profile_name,
                'email': default_profile.email
            }
            
            logger.info(f"Created default profile with ID: {profile_data['id']}")
            return profile_data
            
    except Exception as e:
        logger.error(f"Error creating initial profile: {e}")
        raise


def main():
    """Main setup function."""
    print("🚀 Setting up Job Automation System Database...")
    
    # Configure logging
    configure_logging()
    
    # Get settings
    settings = get_settings()
    logger.info(f"Using database: {settings.db_name}")
    
    # Get database manager
    db_manager = get_database_manager()
    
    try:
        # Test database connection
        print("📡 Testing database connection...")
        if not db_manager.test_connection():
            print("❌ Database connection failed!")
            print(f"   Check your database settings in .env file")
            print(f"   Current URL: {settings.database_url_with_credentials}")
            return False
        
        print("✅ Database connection successful!")
        
        # Create tables
        print("📋 Creating database tables...")
        db_manager.create_tables()
        print("✅ Database tables created!")
        
        # Create initial profile
        print("👤 Creating default user profile...")
        profile_data = create_initial_profile()
        print(f"✅ Default profile created: {profile_data['profile_name']} (ID: {profile_data['id']})")
        
        # Show table information
        print("\n📊 Database Summary:")
        tables = ["user_profiles", "job_postings", "job_applications", "automation_sessions", "error_logs"]
        
        for table in tables:
            try:
                table_info = db_manager.get_table_info(table)
                print(f"   {table}: {table_info['row_count']} rows, {len(table_info['columns'])} columns")
            except Exception as e:
                print(f"   {table}: Error getting info - {e}")
        
        print("\n🎉 Database setup completed successfully!")
        print("\n📝 Next Steps:")
        print("   1. Check pgAdmin to verify tables were created")
        print("   2. Run: python test_phase1.py")
        print("   3. Proceed to Phase 1.2: Core Browser & Profile Management")
        
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        print(f"❌ Database setup failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)