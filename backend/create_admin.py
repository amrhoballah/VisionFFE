#!/usr/bin/env python3
"""
Script to create an admin user for the VisionFFE application.
Run this script after setting up the database to create your first admin user.
"""

import sys
import os
import asyncio
from bson import ObjectId

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_database, init_default_data
from models import User, Role
from auth_utils import get_password_hash, check_password_strength

async def create_admin_user():
    """Create an admin user interactively."""
    print("🔐 VisionFFE Admin User Creation")
    print("=" * 40)
    
    # Initialize database
    await init_database()
    await init_default_data()
    
    try:
        # Check if any admin users already exist
        admin_role = await Role.find_one(Role.name == "admin")
        if admin_role:
            admin_users = await User.find(User.role_ids == admin_role.id).to_list()
            if admin_users:
                print("⚠️  Admin users already exist:")
                for user in admin_users:
                    print(f"   - {user.username} ({user.email})")
                
                response = input("\nDo you want to create another admin user? (y/N): ").strip().lower()
                if response != 'y':
                    print("❌ Admin user creation cancelled.")
                    return
        
        # Get user input
        print("\nPlease provide the following information:")
        username = input("Username: ").strip()
        if not username:
            print("❌ Username cannot be empty.")
            return
        
        email = input("Email: ").strip()
        if not email:
            print("❌ Email cannot be empty.")
            return
        
        password = input("Password: ").strip()
        if not password:
            print("❌ Password cannot be empty.")
            return
        
        # Validate password strength
        password_check = check_password_strength(password)
        if not password_check["is_valid"]:
            print(f"❌ Password validation failed:")
            for issue in password_check["issues"]:
                print(f"   - {issue}")
            return
        
        # Check if username already exists
        existing_user = await User.find_one(User.username == username)
        if existing_user:
            print(f"❌ Username '{username}' already exists.")
            return
        
        # Check if email already exists
        existing_user = await User.find_one(User.email == email)
        if existing_user:
            print(f"❌ Email '{email}' already exists.")
            return
        
        # Create user
        hashed_password = get_password_hash(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True
        )
        
        # Assign admin role
        if admin_role:
            user.role_ids.append(admin_role.id)
        
        await user.insert()
        
        print(f"\n✅ Admin user '{username}' created successfully!")
        print(f"   Email: {email}")
        print(f"   User ID: {user.id}")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")

def main():
    """Main function to run the async admin creation."""
    asyncio.run(create_admin_user())

if __name__ == "__main__":
    main()
