"""
Configuration settings for GeminiMGI
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    google_credentials_path: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "core" / "key.json")
    pdfs_download_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "pdfs_downloaded")
    chromadb_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "chromadb_storage")
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    
    # Google Drive
    drive_folder_id: str = "1B-Xsgvy4W392yfLP4ilrzrtl8zzmEgTl"
    
    # ChromaDB
    chromadb_collection_name: str = "epson_manuals"
    embedding_model_name: str = "intfloat/multilingual-e5-base"
    embedding_batch_size: int = 128
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        self.pdfs_download_dir.mkdir(exist_ok=True)
        self.chromadb_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
