# Date and time utility functions
from datetime import datetime, timedelta
from typing import Optional, Tuple
import re

def format_date_range(start_date: str, end_date: str) -> Tuple[Optional[str], Optional[str]]:
    """Format date range"""
    try:
        # Parse start date
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            start_date = start_dt.isoformat()
        else:
            start_date = None
        
        # Parse end date
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            end_date = end_dt.isoformat()
        else:
            end_date = None
        
        return start_date, end_date
        
    except ValueError:
        return None, None

def parse_relative_date(relative_str: str) -> Optional[datetime]:
    """Parse relative date string"""
    if not relative_str:
        return None
    
    now = datetime.utcnow()
    relative_str = relative_str.lower().strip()
    
    # Today
    if relative_str in ['today', '今天']:
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Yesterday
    if relative_str in ['yesterday', '昨天']:
        return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # This week
    if relative_str in ['this week', '本周']:
        days_since_monday = now.weekday()
        return (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Last week
    if relative_str in ['last week', '上周']:
        days_since_monday = now.weekday()
        last_monday = now - timedelta(days=days_since_monday + 7)
        return last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # This month
    if relative_str in ['this month', '本月']:
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Last month
    if relative_str in ['last month', '上月']:
        if now.month == 1:
            return now.replace(year=now.year-1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            return now.replace(month=now.month-1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Parse "N days ago" format
    days_ago_match = re.search(r'(\d+)\s*days?\s*ago', relative_str)
    if days_ago_match:
        days = int(days_ago_match.group(1))
        return now - timedelta(days=days)
    
    # Parse "N weeks ago" format
    weeks_ago_match = re.search(r'(\d+)\s*weeks?\s*ago', relative_str)
    if weeks_ago_match:
        weeks = int(weeks_ago_match.group(1))
        return now - timedelta(weeks=weeks)
    
    # Parse "N months ago" format
    months_ago_match = re.search(r'(\d+)\s*months?\s*ago', relative_str)
    if months_ago_match:
        months = int(months_ago_match.group(1))
        # Simplified: calculate as 30 days
        return now - timedelta(days=months * 30)
    
    return None

def get_time_range_filters(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    relative_period: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """Get time range filter conditions"""
    
    # If relative period is provided, use it first
    if relative_period:
        relative_start = parse_relative_date(relative_period)
        if relative_start:
            return relative_start.isoformat(), None
    
    # Otherwise use the provided date range
    return format_date_range(start_date or "", end_date or "")

def format_timestamp_for_display(timestamp: str) -> str:
    """Format timestamp for display"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        return timestamp

def get_relative_time_description(timestamp: str) -> str:
    """Get relative time description"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.utcnow()
        diff = now - dt
        
        if diff.days > 0:
            if diff.days == 1:
                return "yesterday"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            elif diff.days < 30:
                weeks = diff.days // 7
                return f"{weeks} weeks ago"
            elif diff.days < 365:
                months = diff.days // 30
                return f"{months} months ago"
            else:
                years = diff.days // 365
                return f"{years} years ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "just now"
            
    except ValueError:
        return "unknown time"

def is_within_time_range(
    timestamp: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> bool:
    """Check if timestamp is within specified range"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if dt < start_dt:
                return False
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            if dt > end_dt:
                return False
        
        return True
        
    except ValueError:
        return False