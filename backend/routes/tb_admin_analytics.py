from fastapi import APIRouter, Depends, Query
from datetime import datetime, timezone, timedelta
from typing import Optional

from backend.models.tb_user import TBUser
from backend.models.tb_credit import TBCreditTransaction
from backend.models.tb_message import TBMessage
from backend.models.tb_payment import TBPayment
from backend.routes.tb_admin_auth import get_current_admin

router = APIRouter(prefix="/api/admin/analytics", tags=["TrueBond Admin Analytics"])


@router.get("/overview")
async def get_overview(
    admin: dict = Depends(get_current_admin)
):
    """Get dashboard overview stats"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # Total users
    total_users = await TBUser.find().count()
    
    # New users today
    new_users_today = await TBUser.find(
        TBUser.created_at >= today_start
    ).count()
    
    # Active users (logged in within 7 days)
    active_users = await TBUser.find(
        {"last_login_at": {"$gte": week_ago}}
    ).count()
    
    # Calculate changes (simplified - comparing to previous period)
    prev_total = await TBUser.find(
        TBUser.created_at < month_ago
    ).count()
    
    user_growth = ((total_users - prev_total) / max(prev_total, 1)) * 100 if prev_total else 100
    
    return {
        "totalUsers": total_users,
        "newUsersToday": new_users_today,
        "activeUsers": active_users,
        "reportsPending": 0,  # Placeholder - no moderation system yet
        "changes": {
            "totalUsers": round(user_growth, 1),
            "newUsers": 8,  # Placeholder
            "activeUsers": 5,  # Placeholder
            "reports": -3  # Placeholder
        }
    }


@router.get("/user-growth")
async def get_user_growth(
    period: str = Query("year", regex="^(week|month|year)$"),
    admin: dict = Depends(get_current_admin)
):
    """Get user growth data for charts"""
    now = datetime.now(timezone.utc)
    
    if period == "week":
        days = 7
        format_key = "%a"  # Mon, Tue, etc.
    elif period == "month":
        days = 30
        format_key = "%d"  # Day number
    else:  # year
        days = 365
        format_key = "%b"  # Jan, Feb, etc.
    
    # Get user counts grouped by date
    start_date = now - timedelta(days=days)
    
    # For simplicity, we'll aggregate manually
    users = await TBUser.find(
        TBUser.created_at >= start_date
    ).to_list()
    
    # Group by formatted date
    from collections import defaultdict
    growth_data = defaultdict(int)
    
    for user in users:
        key = user.created_at.strftime(format_key)
        growth_data[key] += 1
    
    # Convert to list format for chart
    result = [{"period": k, "users": v} for k, v in growth_data.items()]
    
    return {"data": result}


@router.get("/demographics")
async def get_demographics(
    admin: dict = Depends(get_current_admin)
):
    """Get user demographics data"""
    users = await TBUser.find().to_list()
    
    # Age distribution
    age_groups = {"18-24": 0, "25-34": 0, "35-44": 0, "45+": 0}
    for user in users:
        if user.age <= 24:
            age_groups["18-24"] += 1
        elif user.age <= 34:
            age_groups["25-34"] += 1
        elif user.age <= 44:
            age_groups["35-44"] += 1
        else:
            age_groups["45+"] += 1
    
    total = max(len(users), 1)
    age_distribution = [
        {"name": k, "value": round((v / total) * 100), "color": c}
        for (k, v), c in zip(age_groups.items(), ["#E9D5FF", "#0F172A", "#DBEAFE", "#FCE7F3"])
    ]
    
    # Gender distribution
    gender_counts = {"male": 0, "female": 0, "other": 0}
    for user in users:
        gender_counts[user.gender.value] += 1
    
    gender_distribution = [
        {"name": "Male", "value": round((gender_counts["male"] / total) * 100), "color": "#DBEAFE"},
        {"name": "Female", "value": round((gender_counts["female"] / total) * 100), "color": "#FCE7F3"},
        {"name": "Other", "value": round((gender_counts["other"] / total) * 100), "color": "#E9D5FF"},
    ]
    
    return {
        "ageDistribution": age_distribution,
        "genderDistribution": gender_distribution,
        "totalUsers": len(users)
    }


@router.get("/revenue")
async def get_revenue(
    period: str = Query("month", regex="^(week|month|year)$"),
    admin: dict = Depends(get_current_admin)
):
    """Get revenue data"""
    now = datetime.now(timezone.utc)
    
    if period == "week":
        days = 7
    elif period == "month":
        days = 30
    else:
        days = 365
    
    start_date = now - timedelta(days=days)
    
    # Get successful payments
    payments = await TBPayment.find(
        TBPayment.created_at >= start_date,
        TBPayment.status == "success"
    ).to_list()
    
    total_revenue = sum(p.amount_inr for p in payments)
    
    # Group by date for chart
    from collections import defaultdict
    revenue_data = defaultdict(int)
    
    for payment in payments:
        key = payment.created_at.strftime("%b" if period == "year" else "%d")
        revenue_data[key] += payment.amount_inr
    
    return {
        "totalRevenue": total_revenue,
        "data": [{"period": k, "revenue": v} for k, v in revenue_data.items()]
    }


@router.get("/activity")
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50),
    admin: dict = Depends(get_current_admin)
):
    """Get recent platform activity"""
    now = datetime.now(timezone.utc)
    
    # Get recent signups
    recent_users = await TBUser.find().sort("-created_at").limit(limit).to_list()
    
    activities = []
    for user in recent_users:
        # Handle timezone-aware/naive datetime comparison
        created_at = user.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        
        time_diff = now - created_at
        if time_diff.total_seconds() < 60:
            time_str = "Just now"
        elif time_diff.total_seconds() < 3600:
            time_str = f"{int(time_diff.total_seconds() / 60)} mins ago"
        elif time_diff.total_seconds() < 86400:
            time_str = f"{int(time_diff.total_seconds() / 3600)} hours ago"
        else:
            time_str = f"{int(time_diff.total_seconds() / 86400)} days ago"
        
        activities.append({
            "id": str(user.id),
            "type": "signup",
            "user": user.name,
            "time": time_str,
            "avatar": user.name[0].upper()
        })
    
    return {"activities": activities}


@router.get("/highlights")
async def get_highlights(
    admin: dict = Depends(get_current_admin)
):
    """Get today's highlights"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Messages today
    messages_today = await TBMessage.find(
        TBMessage.created_at >= today_start
    ).count()
    
    # Payments today
    payments_today = await TBPayment.find(
        TBPayment.created_at >= today_start,
        TBPayment.status == "success"
    ).to_list()
    
    revenue_today = sum(p.amount_inr for p in payments_today)
    
    return {
        "messagesSent": messages_today,
        "newMatches": 0,  # Placeholder - no matching system
        "coinsPurchased": revenue_today
    }
