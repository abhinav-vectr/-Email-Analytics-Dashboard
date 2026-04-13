"""
SQLAlchemy ORM models for email analytics
Defines the Email model matching the database schema
"""

from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.sql import func
from database import Base


class Email(Base):
    """
    Email model representing the emails table
    Stores email metadata extracted from Gmail
    """
    __tablename__ = "emails"
    
    # Columns
    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String, nullable=False, index=True)
    subject = Column(String)
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_timestamp', 'timestamp'),
        Index('idx_sender', 'sender'),
    )
    
    def __repr__(self):
        return f"<Email(id={self.id}, sender='{self.sender}', subject='{self.subject}', timestamp='{self.timestamp}')>"
