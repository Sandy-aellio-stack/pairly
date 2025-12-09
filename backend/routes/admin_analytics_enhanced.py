from fastapi import APIRouter, Depends, Query, Request, Response
from typing import Optional
import logging
import csv
import io
from datetime import datetime, timezone, timedelta, date
from backend.models.user import User
from backend.models.profile import Profile
from backend.models.credits_transaction import CreditsTransaction
from backend.models.message import Message
from backend.models.post import Post
from backend.models.analytics_snapshot import AnalyticsSnapshot
from backend.services.admin_rbac import get_admin_user, AdminRBACService
from backend.services.admin_logging import AdminLoggingService

logger = logging.getLogger('routes.admin_analytics_enhanced')
router = APIRouter(prefix="/api/admin/analytics", tags=["admin-analytics"])

@router.get("/dashboard")
async def get_analytics_dashboard(
    request: Request,
    admin_user: User = Depends(AdminRBACService.require_permission("analytics.view"))
):
    """Get comprehensive analytics dashboard"""
    try:
        now = datetime.now(timezone.utc)
        today = now.date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Total users
        total_users = await User.count()
        
        # New signups today
        signups_today = await User.find(
            User.created_at >= datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        ).count()
        
        # DAU (users with activity today)
        dau = await User.find(
            User.updated_at >= datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        ).count()
        
        # WAU (users with activity in last 7 days)
        wau = await User.find(
            User.updated_at >= datetime.combine(week_ago, datetime.min.time()).replace(tzinfo=timezone.utc)
        ).count()
        
        # MAU (users with activity in last 30 days)
        mau = await User.find(
            User.updated_at >= datetime.combine(month_ago, datetime.min.time()).replace(tzinfo=timezone.utc)
        ).count()
        
        # Messages today
        messages_today = await Message.find(
            Message.sent_at >= datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        ).count()
        
        # Total revenue (from credits transactions)
        revenue_transactions = await CreditsTransaction.find(
            CreditsTransaction.transaction_type == "purchase"
        ).to_list()
        total_revenue = sum(t.amount for t in revenue_transactions if t.amount > 0)
        
        # Creator count
        creator_count = await User.find(User.role == "creator").count()
        
        dashboard = {
            "user_metrics": {
                "total_users": total_users,
                "signups_today": signups_today,
                "dau": dau,
                "wau": wau,
                "mau": mau
            },
            "engagement_metrics": {
                "messages_today": messages_today
            },
            "financial_metrics": {
                "total_revenue": total_revenue,
                "creator_count": creator_count
            },
            "timestamp": now.isoformat()
        }
        
        await AdminLoggingService.log_action(
            admin_user_id=str(admin_user.id),
            admin_email=admin_user.email,
            admin_role=admin_user.role,
            action="analytics_dashboard_viewed",
            target_type="system",
            ip_address=request.client.host if request.client else None
        )
        
        return dashboard
        
    except Exception as e:
        logger.error(f"Error fetching analytics dashboard: {e}", exc_info=True)
        return {"error": str(e)}

@router.get("/metrics/dau-wau-mau")
async def get_dau_wau_mau(
    request: Request,
    days: int = Query(30, ge=1, le=90),
    admin_user: User = Depends(AdminRBACService.require_permission("analytics.view"))
):
    """Get DAU, WAU, MAU metrics over time"""
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=days)
    
    # Get snapshots from database
    snapshots = await AnalyticsSnapshot.find(
        AnalyticsSnapshot.snapshot_date >= start_date,
        AnalyticsSnapshot.snapshot_type == "daily"
    ).sort("snapshot_date").to_list()
    
    return {
        "metrics": [
            {
                "date": snap.snapshot_date.isoformat(),
                "dau": snap.dau,
                "wau": snap.wau,
                "mau": snap.mau
            }
            for snap in snapshots
        ],
        "period_days": days
    }

@router.get("/metrics/retention")
async def get_retention_metrics(
    request: Request,
    admin_user: User = Depends(AdminRBACService.require_permission("analytics.view"))
):
    """Get user retention metrics (D1, D7, D30)"""
    try:
        # Get users from 30 days ago
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
        
        # Users who signed up 30 days ago
        cohort_30 = await User.find(
            User.created_at >= thirty_days_ago - timedelta(days=1),
            User.created_at < thirty_days_ago
        ).to_list()
        
        # How many are still active
        if cohort_30:
            active_30 = await User.find(
                {"id": {"$in": [u.id for u in cohort_30]},
                 "updated_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=1)}}
            ).count()
            retention_d30 = (active_30 / len(cohort_30)) * 100
        else:
            retention_d30 = 0
        
        # Similar calculations for D7 and D1
        cohort_7 = await User.find(
            User.created_at >= seven_days_ago - timedelta(days=1),
            User.created_at < seven_days_ago
        ).to_list()
        
        if cohort_7:
            active_7 = await User.find(
                {"id": {"$in": [u.id for u in cohort_7]},
                 "updated_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=1)}}
            ).count()
            retention_d7 = (active_7 / len(cohort_7)) * 100
        else:
            retention_d7 = 0
        
        cohort_1 = await User.find(
            User.created_at >= one_day_ago - timedelta(hours=24),
            User.created_at < one_day_ago
        ).to_list()
        
        if cohort_1:
            active_1 = await User.find(
                {"id": {"$in": [u.id for u in cohort_1]},
                 "updated_at": {"$gte": datetime.now(timezone.utc) - timedelta(hours=24)}}
            ).count()
            retention_d1 = (active_1 / len(cohort_1)) * 100
        else:
            retention_d1 = 0
        
        return {
            "retention": {
                "d1": round(retention_d1, 2),
                "d7": round(retention_d7, 2),
                "d30": round(retention_d30, 2)
            },
            "cohort_sizes": {
                "d1_cohort": len(cohort_1),
                "d7_cohort": len(cohort_7),
                "d30_cohort": len(cohort_30)
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating retention: {e}", exc_info=True)
        return {"error": str(e)}

@router.get("/metrics/churn")
async def get_churn_rate(
    request: Request,
    admin_user: User = Depends(AdminRBACService.require_permission("analytics.view"))
):
    """Calculate churn rate"""
    try:
        # Users who were active 30 days ago
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        sixty_days_ago = datetime.now(timezone.utc) - timedelta(days=60)
        
        # Users active between 30-60 days ago
        cohort = await User.find(
            User.updated_at >= sixty_days_ago,
            User.updated_at < thirty_days_ago
        ).to_list()
        
        if not cohort:
            return {"churn_rate": 0, "note": "No cohort data available"}
        
        # How many are no longer active
        inactive = await User.find(
            {"id": {"$in": [u.id for u in cohort]},
             "updated_at": {"$lt": datetime.now(timezone.utc) - timedelta(days=30)}}
        ).count()
        
        churn_rate = (inactive / len(cohort)) * 100
        
        return {
            "churn_rate": round(churn_rate, 2),
            "cohort_size": len(cohort),
            "churned_users": inactive
        }
        
    except Exception as e:
        logger.error(f"Error calculating churn: {e}", exc_info=True)
        return {"error": str(e)}

@router.get("/metrics/acquisition")
async def get_acquisition_metrics(
    request: Request,
    days: int = Query(30, ge=1, le=90),
    admin_user: User = Depends(AdminRBACService.require_permission("analytics.view"))
):
    """Get user acquisition metrics"""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Daily signups
    signups = await User.find(
        User.created_at >= start_date
    ).to_list()
    
    # Group by date
    daily_signups = {}
    for user in signups:
        date_key = user.created_at.date().isoformat()
        daily_signups[date_key] = daily_signups.get(date_key, 0) + 1
    
    return {
        "daily_signups": [
            {"date": date, "signups": count}
            for date, count in sorted(daily_signups.items())
        ],
        "total_signups": len(signups),
        "period_days": days
    }

@router.get("/metrics/feature-usage")
async def get_feature_usage(
    request: Request,
    admin_user: User = Depends(AdminRBACService.require_permission("analytics.view"))
):
    """Get feature usage metrics"""
    today = datetime.now(timezone.utc).date()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    
    messages_today = await Message.find(
        Message.sent_at >= today_start
    ).count()
    
    posts_today = await Post.find(
        Post.created_at >= today_start
    ).count()
    
    return {
        "feature_usage": {
            "messages_sent": messages_today,
            "posts_created": posts_today,
            "swipes": 0,  # TODO: Implement swipe tracking
            "matches": 0,  # TODO: Implement match tracking
            "calls": 0  # TODO: Implement call tracking
        },
        "date": today.isoformat()
    }

@router.get("/metrics/creator-earnings")
async def get_creator_earnings(
    request: Request,
    days: int = Query(30, ge=1, le=90),
    admin_user: User = Depends(AdminRBACService.require_permission("analytics.view"))
):
    """Get creator earnings analytics"""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Get all creator earnings transactions
    earnings = await CreditsTransaction.find(
        CreditsTransaction.transaction_type == "message_earnings",
        CreditsTransaction.created_at >= start_date
    ).to_list()
    
    # Group by user
    creator_earnings = {}
    for transaction in earnings:
        user_id = str(transaction.user_id)
        creator_earnings[user_id] = creator_earnings.get(user_id, 0) + transaction.amount
    
    # Get top earners
    top_earners = sorted(creator_earnings.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "total_earnings": sum(creator_earnings.values()),
        "creator_count": len(creator_earnings),
        "top_earners": [
            {"user_id": user_id, "earnings": earnings}
            for user_id, earnings in top_earners
        ],
        "period_days": days
    }

@router.get("/funnel")
async def get_conversion_funnel(
    request: Request,
    admin_user: User = Depends(AdminRBACService.require_permission("analytics.view"))
):
    """Get conversion funnel metrics"""
    total_users = await User.count()
    users_with_profile = await Profile.count()
    users_with_messages = await Message.distinct("sender_id")
    
    return {
        "funnel": [
            {"stage": "signup", "count": total_users, "conversion": 100.0},
            {"stage": "profile_created", "count": users_with_profile, 
             "conversion": round((users_with_profile / total_users * 100), 2) if total_users > 0 else 0},
            {"stage": "first_message", "count": len(users_with_messages),
             "conversion": round((len(users_with_messages) / total_users * 100), 2) if total_users > 0 else 0}
        ]
    }

@router.get("/export/json")
async def export_analytics_json(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    admin_user: User = Depends(AdminRBACService.require_permission("analytics.export"))
):
    """Export analytics data as JSON"""
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=days)
    
    snapshots = await AnalyticsSnapshot.find(
        AnalyticsSnapshot.snapshot_date >= start_date
    ).sort("snapshot_date").to_list()
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin_user.id),
        admin_email=admin_user.email,
        admin_role=admin_user.role,
        action="analytics_exported_json",
        target_type="analytics",
        metadata={"days": days, "snapshots_count": len(snapshots)},
        ip_address=request.client.host if request.client else None
    )
    
    return {
        "data": [
            {
                "date": snap.snapshot_date.isoformat(),
                "total_users": snap.total_users,
                "dau": snap.dau,
                "wau": snap.wau,
                "mau": snap.mau,
                "new_signups": snap.new_signups_today,
                "revenue": snap.total_revenue
            }
            for snap in snapshots
        ],
        "period_days": days,
        "export_date": datetime.now(timezone.utc).isoformat()
    }

@router.get("/export/csv")
async def export_analytics_csv(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    admin_user: User = Depends(AdminRBACService.require_permission("analytics.export"))
):
    """Export analytics data as CSV"""
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=days)
    
    snapshots = await AnalyticsSnapshot.find(
        AnalyticsSnapshot.snapshot_date >= start_date
    ).sort("snapshot_date").to_list()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Date', 'Total Users', 'DAU', 'WAU', 'MAU', 'New Signups', 'Revenue'])
    
    # Data
    for snap in snapshots:
        writer.writerow([
            snap.snapshot_date.isoformat(),
            snap.total_users,
            snap.dau,
            snap.wau,
            snap.mau,
            snap.new_signups_today,
            snap.total_revenue
        ])
    
    await AdminLoggingService.log_action(
        admin_user_id=str(admin_user.id),
        admin_email=admin_user.email,
        admin_role=admin_user.role,
        action="analytics_exported_csv",
        target_type="analytics",
        metadata={"days": days, "snapshots_count": len(snapshots)},
        ip_address=request.client.host if request.client else None
    )
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=analytics_{start_date}_{end_date}.csv"}
    )