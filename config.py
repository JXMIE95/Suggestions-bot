import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    """Configuration class for the Discord bot"""
    
    def __init__(self):
        self.DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
        self.SUGGESTION_CHANNEL_ID = self._get_channel_id("SUGGESTION_CHANNEL_ID")
        self.STAFF_CHANNEL_ID = self._get_channel_id("STAFF_CHANNEL_ID")
        self.APPROVED_CHANNEL_ID = self._get_channel_id("APPROVED_CHANNEL_ID")
        self.APPROVED_ROLE_ID = self._get_role_id("APPROVED_ROLE_ID")
        
        # Optional configuration
        self.BOT_PREFIX = os.getenv("BOT_PREFIX", "!")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
        # Validate required configuration
        self._validate_config()
    
    def _get_channel_id(self, env_var: str) -> int:
        """Get channel ID from environment variable"""
        channel_id = os.getenv(env_var)
        if not channel_id:
            logger.warning(f"{env_var} not set in environment variables")
            return None
        
        try:
            return int(channel_id)
        except ValueError:
            logger.error(f"Invalid {env_var}: {channel_id} is not a valid integer")
            return None
    
    def _get_role_id(self, env_var: str) -> int:
        """Get role ID from environment variable"""
        role_id = os.getenv(env_var)
        if not role_id:
            logger.warning(f"{env_var} not set in environment variables")
            return None
        
        try:
            return int(role_id)
        except ValueError:
            logger.error(f"Invalid {env_var}: {role_id} is not a valid integer")
            return None
    
    def _validate_config(self):
        """Validate required configuration"""
        if not self.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN is required in environment variables")
        
        if not self.SUGGESTION_CHANNEL_ID:
            logger.warning("SUGGESTION_CHANNEL_ID not configured - suggestion command will not work")
        
        if not self.STAFF_CHANNEL_ID:
            logger.warning("STAFF_CHANNEL_ID not configured - tickets will not be created")
        
        if not self.APPROVED_CHANNEL_ID:
            logger.warning("APPROVED_CHANNEL_ID not configured - approved suggestions will not be posted")
        
        if not self.APPROVED_ROLE_ID:
            logger.warning("APPROVED_ROLE_ID not configured - role will not be mentioned for approved suggestions")
    
    def __repr__(self):
        return f"Config(suggestion_channel={self.SUGGESTION_CHANNEL_ID}, staff_channel={self.STAFF_CHANNEL_ID})"
