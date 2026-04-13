"""
FastAPI Backend for Email Analytics Dashboard
Provides REST API endpoints for email analytics and statistics
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, desc
from datetime import datetime
from collections import Counter
import re

from backend.database import get_db, engine
from backend.models import Base, Email

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Email Analytics API",
    description="REST API for Gmail inbox analytics",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "*"  # In production, replace with your actual frontend domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
def root():
    """Root endpoint - API information"""
    return {
        "message": "Email Analytics API",
        "version": "1.0.0",
        "endpoints": [
            "/total-emails",
            "/unique-senders",
            "/top-senders",
            "/emails-per-day",
            "/emails-per-hour",
            "/emails-per-weekday",
            "/domain-distribution",
            "/subject-keywords",
            "/date-range",
            "/summary"
        ]
    }


@app.get("/total-emails")
def get_total_emails(db: Session = Depends(get_db)):
    """
    Get total number of emails in database
    Returns: {"total": int}
    """
    try:
        total = db.query(func.count(Email.id)).scalar()
        return {"total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/unique-senders")
def get_unique_senders(db: Session = Depends(get_db)):
    """
    Get count of unique email senders
    Returns: {"unique_senders": int}
    """
    try:
        unique = db.query(func.count(func.distinct(Email.sender))).scalar()
        return {"unique_senders": unique}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/top-senders")
def get_top_senders(limit: int = 10, db: Session = Depends(get_db)):
    """
    Get top email senders by count
    Query params: limit (default: 10)
    Returns: [{"sender": str, "count": int}, ...]
    """
    try:
        results = (
            db.query(
                Email.sender,
                func.count(Email.id).label('count')
            )
            .group_by(Email.sender)
            .order_by(desc('count'))
            .limit(limit)
            .all()
        )
        
        return [
            {"sender": sender, "count": count}
            for sender, count in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/emails-per-day")
def get_emails_per_day(db: Session = Depends(get_db)):
    """
    Get email count grouped by day
    Returns: [{"date": str, "count": int}, ...]
    """
    try:
        results = (
            db.query(
                func.date(Email.timestamp).label('date'),
                func.count(Email.id).label('count')
            )
            .group_by(func.date(Email.timestamp))
            .order_by('date')
            .all()
        )
        
        return [
            {"date": str(date), "count": count}
            for date, count in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/emails-per-hour")
def get_emails_per_hour(db: Session = Depends(get_db)):
    """
    Get email count grouped by hour of day (0-23)
    Returns: [{"hour": int, "count": int}, ...]
    """
    try:
        results = (
            db.query(
                extract('hour', Email.timestamp).label('hour'),
                func.count(Email.id).label('count')
            )
            .group_by('hour')
            .order_by('hour')
            .all()
        )
        
        # Fill in missing hours with 0 count
        hour_counts = {int(hour): count for hour, count in results}
        return [
            {"hour": hour, "count": hour_counts.get(hour, 0)}
            for hour in range(24)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/emails-per-weekday")
def get_emails_per_weekday(db: Session = Depends(get_db)):
    """
    Get email count grouped by day of week
    Returns: [{"day": str, "count": int}, ...]
    0 = Sunday, 1 = Monday, ..., 6 = Saturday
    """
    try:
        results = (
            db.query(
                extract('dow', Email.timestamp).label('dow'),
                func.count(Email.id).label('count')
            )
            .group_by('dow')
            .order_by('dow')
            .all()
        )
        
        # Map day numbers to names
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        day_counts = {int(dow): count for dow, count in results}
        
        return [
            {"day": day_names[day], "count": day_counts.get(day, 0)}
            for day in range(7)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/domain-distribution")
def get_domain_distribution(db: Session = Depends(get_db)):
    """
    Get distribution of email domains
    Returns: [{"domain": str, "count": int}, ...]
    """
    try:
        # Get all senders
        senders = db.query(Email.sender).all()
        
        # Extract domains
        domains = []
        for (sender,) in senders:
            # Extract domain from email address
            if '@' in sender:
                domain = sender.split('@')[1].lower()
                domains.append(domain)
            else:
                domains.append('unknown')
        
        # Count domains
        domain_counts = Counter(domains)
        
        # Return top domains
        return [
            {"domain": domain, "count": count}
            for domain, count in domain_counts.most_common(15)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/subject-keywords")
def get_subject_keywords(limit: int = 20, db: Session = Depends(get_db)):
    """
    Get most common keywords in email subjects
    Query params: limit (default: 20)
    Returns: [{"keyword": str, "count": int}, ...]
    """
    try:
        # Get all subjects
        subjects = db.query(Email.subject).filter(Email.subject.isnot(None)).all()
        
        # Extract words from subjects
        words = []
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                      'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
                      'your', 'you', 'this', 'that', 'it', 'as', 'has', 'have', 'had', 're'}
        
        for (subject,) in subjects:
            if subject:
                # Extract words (alphanumeric only, lowercase)
                subject_words = re.findall(r'\b[a-zA-Z]{3,}\b', subject.lower())
                # Filter out stop words
                filtered_words = [w for w in subject_words if w not in stop_words]
                words.extend(filtered_words)
        
        # Count words
        word_counts = Counter(words)
        
        return [
            {"keyword": word, "count": count}
            for word, count in word_counts.most_common(limit)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/date-range")
def get_date_range(db: Session = Depends(get_db)):
    """
    Get the date range of emails in database
    Returns: {"first_email": str, "last_email": str, "days_covered": int}
    """
    try:
        first_email = db.query(func.min(Email.timestamp)).scalar()
        last_email = db.query(func.max(Email.timestamp)).scalar()
        
        if first_email and last_email:
            days_covered = (last_email - first_email).days + 1
            return {
                "first_email": str(first_email),
                "last_email": str(last_email),
                "days_covered": days_covered
            }
        else:
            return {
                "first_email": None,
                "last_email": None,
                "days_covered": 0
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    """
    Get summary statistics combining multiple metrics
    Returns: Combined summary object
    """
    try:
        # Total emails
        total = db.query(func.count(Email.id)).scalar()
        
        # Unique senders
        unique_senders = db.query(func.count(func.distinct(Email.sender))).scalar()
        
        # Date range
        first_email = db.query(func.min(Email.timestamp)).scalar()
        last_email = db.query(func.max(Email.timestamp)).scalar()
        
        # Top sender
        top_sender_result = (
            db.query(
                Email.sender,
                func.count(Email.id).label('count')
            )
            .group_by(Email.sender)
            .order_by(desc('count'))
            .first()
        )
        
        top_sender = None
        top_sender_count = 0
        if top_sender_result:
            top_sender, top_sender_count = top_sender_result
        
        # Calculate days covered
        days_covered = 0
        if first_email and last_email:
            days_covered = (last_email - first_email).days + 1
        
        return {
            "total_emails": total,
            "unique_senders": unique_senders,
            "first_email": str(first_email) if first_email else None,
            "last_email": str(last_email) if last_email else None,
            "days_covered": days_covered,
            "top_sender": top_sender,
            "top_sender_count": top_sender_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
