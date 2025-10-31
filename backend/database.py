from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from auth_config import auth_settings
from models import User, Role, Permission, Token, Project
import asyncio
import ssl
import certifi

# Global MongoDB client
client: AsyncIOMotorClient = None


async def init_database():
    """Initialize MongoDB connection and Beanie."""
    global client

    try:
        # Detect if using MongoDB Atlas (requires TLS)
        is_atlas = "mongodb+srv://" in auth_settings.mongodb_url

        # Build connection parameters
        connection_kwargs = {
            "serverSelectionTimeoutMS": 10000,
            "connectTimeoutMS": 10000,
            "socketTimeoutMS": 10000,
            "retryWrites": True,
            "maxPoolSize": 10,
            "minPoolSize": 1,
            "retryReads": True
        }

        # Atlas requires TLS with a trusted CA
        if is_atlas:
            connection_kwargs.update({
                "tls": True,
                "tlsCAFile": certifi.where(),  # replaces ssl_ca_certs / ssl_certfile
                "tlsAllowInvalidCertificates": False  # set to True only for debugging
            })

        # Local Mongo (no TLS)
        else:
            connection_kwargs.update({
                "tls": False
            })

        # Create MongoDB client
        client = AsyncIOMotorClient(
            auth_settings.mongodb_url,
            tls=True,
            tlsCAFile=certifi.where(),
            tlsAllowInvalidCertificates=False
        )

        # Test connection
        await client.admin.command("ping")
        print("✅ MongoDB connection successful")

        # Initialize Beanie with the database
        await init_beanie(
            database=client[auth_settings.mongodb_database],
            document_models=[User, Role, Permission, Token, Project]
        )

        print("✅ MongoDB database initialized")

    except Exception as e:
        print(f"❌ Error initializing MongoDB: {e}")
        if client:
            client.close()
        raise


async def close_database():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        print("✅ MongoDB connection closed")


async def init_default_data():
    """Initialize default roles and permissions."""
    try:
        # Check if roles already exist
        existing_role = await Role.find_one()
        if existing_role:
            return

        # Create default permissions
        permissions = [
            Permission(
                name="admin_all",
                description="Full administrative access",
                resource="*",
                action="*"
            ),
            Permission(
                name="search_images",
                description="Search for similar images",
                resource="images",
                action="read"
            ),
            Permission(
                name="upload_images",
                description="Upload new images",
                resource="images",
                action="write"
            ),
            Permission(
                name="view_stats",
                description="View database statistics",
                resource="stats",
                action="read"
            ),
            Permission(
                name="search_images_view",
                description="Search for similar images (view only)",
                resource="images",
                action="read"
            ),
            Permission(
                name="view_stats_view",
                description="View database statistics (view only)",
                resource="stats",
                action="read"
            ),
        ]

        # Insert permissions
        for permission in permissions:
            await permission.insert()

        # Create default roles
        admin_role = Role(
            name="admin",
            description="Administrator with full access",
            permission_ids=[permissions[0].id]
        )

        user_role = Role(
            name="user",
            description="Regular user with limited access",
            permission_ids=[permissions[1].id, permissions[2].id, permissions[3].id]
        )

        viewer_role = Role(
            name="viewer",
            description="Read-only access",
            permission_ids=[permissions[4].id, permissions[5].id]
        )

        designer_role = Role(
            name="designer",
            description="Designer role with extractor access",
            permission_ids=[permissions[1].id, permissions[2].id, permissions[3].id]
        )

        # Insert roles
        await admin_role.insert()
        await user_role.insert()
        await viewer_role.insert()
        await designer_role.insert()

        print("✅ Default roles and permissions created")

    except Exception as e:
        print(f"⚠️ Error initializing default data: {e}")


def get_db():
    """Dependency to get database session (MongoDB doesn't need sessions)."""
    return None
