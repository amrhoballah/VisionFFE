"""
Migration script to update existing users with default values for new fields.
Run this once to update existing users in the database.
"""

import asyncio
from beanie import init_beanie
from pymongo import AsyncMongoClient
from models import User
import os
from dotenv import load_dotenv

load_dotenv()

async def migrate_users():
    """Update existing users with default values for new fields."""
    
    # Connect to MongoDB
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        raise ValueError("MONGODB_URL environment variable is not set")
    
    client = AsyncMongoClient(mongodb_url)
    database = client[os.getenv("MONGODB_DB_NAME", "visionffe")]

    await init_beanie(database=database, document_models=[User])
    
    print("🔍 Finding users that need migration...")
    
    # Find all users without the new fields
    users_to_update = await User.find({
        "$or": [
            {"firstName": {"$exists": False}},
            {"lastName": {"$exists": False}},
            {"title": {"$exists": False}},
            {"location": {"$exists": False}},
            {"phone": {"$exists": False}}
        ]
    }).to_list()
    
    print(f"Found {len(users_to_update)} users to update")
    
    if len(users_to_update) == 0:
        print("✅ No users need migration. All good!")
        return
    
    # Update each user
    updated_count = 0
    for user in users_to_update:
        try:
            # Check if fields are missing and set defaults
            update_data = {}
            
            if not hasattr(user, 'firstName') or user.firstName == "":
                update_data['firstName'] = ""
            
            if not hasattr(user, 'lastName') or user.lastName == "":
                update_data['lastName'] = ""
            
            if not hasattr(user, 'title') or user.title == "":
                update_data['title'] = ""
            
            if not hasattr(user, 'location') or user.location == "":
                update_data['location'] = ""
            
            if not hasattr(user, 'phone') or user.phone == "":
                update_data['phone'] = ""
            
            # Update the user if needed
            if update_data:
                for key, value in update_data.items():
                    setattr(user, key, value)
                await user.save()
                updated_count += 1
                print(f"✅ Updated user: {user.username}")
        
        except Exception as e:
            print(f"❌ Error updating user {user.username}: {e}")
    
    print(f"\n🎉 Migration complete! Updated {updated_count} users")
    
    # Close connection
    client.close()

if __name__ == "__main__":
    print("🚀 Starting user migration...")
    asyncio.run(migrate_users())

