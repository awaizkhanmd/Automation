"""
Command-line interface for profile management.

This script provides a CLI for creating, viewing, and managing
user profiles for the job automation system.
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.core.profile_manager import ProfileManager
from src.utils.logger import configure_logging


def create_profile_interactive():
    """Create a new profile through interactive prompts."""
    print("🆕 Creating New Profile")
    print("=" * 30)
    
    profile_data = {}
    
    # Basic information
    profile_data['profile_name'] = input("Profile name: ").strip()
    profile_data['first_name'] = input("First name: ").strip()
    profile_data['last_name'] = input("Last name: ").strip()
    profile_data['email'] = input("Email: ").strip()
    profile_data['phone'] = input("Phone (optional): ").strip() or None
    profile_data['location'] = input("Location: ").strip()
    
    # Professional information
    profile_data['current_title'] = input("Current job title: ").strip()
    
    target_roles_input = input("Target roles (comma-separated): ").strip()
    profile_data['target_roles'] = [role.strip() for role in target_roles_input.split(',') if role.strip()]
    
    skills_input = input("Skills (comma-separated): ").strip()
    profile_data['skills'] = [skill.strip() for skill in skills_input.split(',') if skill.strip()]
    
    try:
        profile_data['experience_years'] = int(input("Years of experience: ").strip())
    except ValueError:
        profile_data['experience_years'] = 0
    
    # Job preferences
    locations_input = input("Preferred locations (comma-separated): ").strip()
    profile_data['preferred_locations'] = [loc.strip() for loc in locations_input.split(',') if loc.strip()]
    
    profile_data['remote_preference'] = input("Remote preference (remote/hybrid/onsite/any): ").strip() or "any"
    
    try:
        profile_data['salary_min'] = int(input("Minimum salary: ").strip())
        profile_data['salary_max'] = int(input("Maximum salary: ").strip())
    except ValueError:
        profile_data['salary_min'] = None
        profile_data['salary_max'] = None
    
    job_types_input = input("Job types (full_time, contract, part_time): ").strip()
    profile_data['job_types'] = [jt.strip() for jt in job_types_input.split(',') if jt.strip()]
    
    # Site preferences
    sites_input = input("Preferred job sites (linkedin, indeed, dice): ").strip()
    profile_data['preferred_sites'] = [site.strip() for site in sites_input.split(',') if site.strip()]
    
    # Automation settings
    try:
        profile_data['max_applications_per_day'] = int(input("Max applications per day (default 50): ").strip() or "50")
        profile_data['application_delay_seconds'] = int(input("Delay between applications in seconds (default 3): ").strip() or "3")
    except ValueError:
        profile_data['max_applications_per_day'] = 50
        profile_data['application_delay_seconds'] = 3
    
    return profile_data


def list_profiles(profile_manager: ProfileManager):
    """List all profiles."""
    print("📋 User Profiles")
    print("=" * 50)
    
    profiles = profile_manager.list_profiles()
    
    if not profiles:
        print("No profiles found.")
        return
    
    for profile in profiles:
        status = "🟢" if profile['is_active'] else "🔴"
        print(f"{status} {profile['profile_name']} (ID: {profile['id']})")
        print(f"   Name: {profile['first_name']} {profile['last_name']}")
        print(f"   Email: {profile['email']}")
        print(f"   Target roles: {', '.join(profile.get('target_roles', []))}")
        print(f"   Preferred sites: {', '.join(profile.get('preferred_sites', []))}")
        print()


def view_profile(profile_manager: ProfileManager, profile_identifier: str):
    """View detailed profile information."""
    profile = profile_manager.load_profile(profile_identifier)
    
    if not profile:
        print(f"❌ Profile not found: {profile_identifier}")
        return
    
    print(f"👤 Profile: {profile.profile_name}")
    print("=" * 50)
    
    print("📋 Personal Information:")
    print(f"   Name: {profile.first_name} {profile.last_name}")
    print(f"   Email: {profile.email}")
    print(f"   Phone: {profile.phone or 'Not provided'}")
    print(f"   Location: {profile.location or 'Not provided'}")
    
    print("\n💼 Professional Information:")
    print(f"   Current title: {profile.current_title or 'Not provided'}")
    print(f"   Experience: {profile.experience_years or 0} years")
    print(f"   Target roles: {', '.join(profile.target_roles or [])}")
    print(f"   Skills: {', '.join(profile.skills or [])}")
    
    print("\n🎯 Job Preferences:")
    print(f"   Preferred locations: {', '.join(profile.preferred_locations or [])}")
    print(f"   Remote preference: {profile.remote_preference or 'any'}")
    print(f"   Salary range: ${profile.salary_min or 0:,} - ${profile.salary_max or 0:,}")
    print(f"   Job types: {', '.join(profile.job_types or [])}")
    
    print("\n🤖 Automation Settings:")
    print(f"   Max applications per day: {profile.max_applications_per_day or 50}")
    print(f"   Application delay: {profile.application_delay_seconds or 3} seconds")
    print(f"   Preferred sites: {', '.join(profile.preferred_sites or [])}")
    
    print("\n📊 Metadata:")
    print(f"   Status: {'Active' if profile.is_active else 'Inactive'}")
    print(f"   Created: {profile.created_at}")
    print(f"   Updated: {profile.updated_at}")


def export_profile(profile_manager: ProfileManager, profile_identifier: str, output_path: str = None):
    """Export profile to JSON file."""
    profile = profile_manager.load_profile(profile_identifier)
    
    if not profile:
        print(f"❌ Profile not found: {profile_identifier}")
        return
    
    export_path = profile_manager.export_profile(profile.id, output_path)
    
    if export_path:
        print(f"✅ Profile exported to: {export_path}")
    else:
        print("❌ Export failed")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Job Automation Profile Manager CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List profiles command
    subparsers.add_parser('list', help='List all profiles')
    
    # View profile command
    view_parser = subparsers.add_parser('view', help='View profile details')
    view_parser.add_argument('profile', help='Profile name or ID')
    
    # Create profile command
    subparsers.add_parser('create', help='Create new profile interactively')
    
    # Export profile command
    export_parser = subparsers.add_parser('export', help='Export profile to JSON')
    export_parser.add_argument('profile', help='Profile name or ID')
    export_parser.add_argument('--output', '-o', help='Output file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Configure logging
    configure_logging()
    
    # Initialize profile manager
    profile_manager = ProfileManager()
    
    try:
        if args.command == 'list':
            list_profiles(profile_manager)
            
        elif args.command == 'view':
            view_profile(profile_manager, args.profile)
            
        elif args.command == 'create':
            profile_data = create_profile_interactive()
            profile = profile_manager.create_profile(profile_data)
            
            if profile:
                print(f"\n✅ Profile created successfully!")
                print(f"Profile ID: {profile.id}")
                print(f"Profile name: {profile.profile_name}")
            else:
                print("\n❌ Profile creation failed")
                
        elif args.command == 'export':
            export_profile(profile_manager, args.profile, args.output)
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()