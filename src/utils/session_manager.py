"""
Session Manager - Helper for managing persistent sessions with DatabaseSessionService
"""

import logging
from typing import Optional
from google.adk.sessions import DatabaseSessionService, InMemorySessionService
from .config import Config

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages session services for the medical bill processing system.
    Provides easy access to persistent or in-memory sessions.
    """

    @staticmethod
    def create_session_service(use_database: bool = True, db_url: Optional[str] = None):
        """
        Create a session service (persistent or in-memory).

        Args:
            use_database: If True, use DatabaseSessionService, else InMemorySessionService
            db_url: Optional database URL override

        Returns:
            Session service instance
        """
        if use_database:
            url = db_url or Config.DATABASE_URL
            logger.info(f"🗄️  Creating DatabaseSessionService")
            logger.info(f"   Database: {url}")

            try:
                session_service = DatabaseSessionService(db_url=url)
                logger.info(f"✅ Persistent sessions enabled")
                return session_service
            except ValueError as e:
                if "asyncio extension requires an async driver" in str(e) or "pysqlite" in str(e):
                    logger.error("❌ Async database driver not found!")
                    logger.error("   For SQLite, you need 'aiosqlite'")
                    logger.error("   Install it with: pip install aiosqlite")
                    logger.error("   Database URL should be: sqlite+aiosqlite:///your_db.db")
                    raise ValueError(
                        "Async SQLite driver 'aiosqlite' is required. "
                        "Install it with: pip install aiosqlite"
                    ) from e
                else:
                    raise
        else:
            logger.info(f"💾 Creating InMemorySessionService")
            session_service = InMemorySessionService()
            logger.info(f"✅ In-memory sessions enabled (no persistence)")
            return session_service

    @staticmethod
    def get_session_info():
        """Get information about session configuration."""
        return {
            "database_url": Config.DATABASE_URL,
            "app_name": Config.APP_NAME,
            "compaction_enabled": True,
            "compaction_interval": Config.COMPACTION_INTERVAL,
            "overlap_size": Config.OVERLAP_SIZE
        }

    @staticmethod
    def print_session_info(session_service):
        """Print session service information."""
        info = SessionManager.get_session_info()

        print("\n" + "="*80)
        print("SESSION SERVICE CONFIGURATION")
        print("="*80)

        if isinstance(session_service, DatabaseSessionService):
            print(f"📊 Session Type: Persistent Database")
            print(f"🗄️  Database URL: {info['database_url']}")
            print(f"💾 Persistence: Sessions will survive restarts")
        else:
            print(f"📊 Session Type: In-Memory")
            print(f"💾 Persistence: Sessions cleared on restart")

        print(f"\n📱 App Name: {info['app_name']}")
        print(f"🔄 Events Compaction: {'Enabled' if info['compaction_enabled'] else 'Disabled'}")

        if info['compaction_enabled']:
            print(f"   • Compaction Interval: {info['compaction_interval']} invocations")
            print(f"   • Overlap Size: {info['overlap_size']} turns")

        print("="*80 + "\n")

