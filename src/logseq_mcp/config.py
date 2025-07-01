"""Configuration module for Logseq MCP server."""
import os
from typing import Optional


class Config:
    """Configuration settings for the Logseq MCP server."""
    
    # API Configuration
    LOGSEQ_API_URL: str = os.getenv("LOGSEQ_API_URL", "http://localhost:12315")
    LOGSEQ_TOKEN: Optional[str] = os.getenv("LOGSEQ_TOKEN")
    
    # Graph Configuration
    LOGSEQ_GRAPH_PATH: Optional[str] = os.getenv("LOGSEQ_GRAPH_PATH")
    
    # Performance Configuration
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes default
    MAX_BATCH_SIZE: int = int(os.getenv("MAX_BATCH_SIZE", "50"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration settings."""
        if cls.LOGSEQ_GRAPH_PATH and not os.path.exists(cls.LOGSEQ_GRAPH_PATH):
            raise ValueError(f"LOGSEQ_GRAPH_PATH does not exist: {cls.LOGSEQ_GRAPH_PATH}")


# Create a singleton instance
config = Config()