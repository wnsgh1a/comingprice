from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import logging
from db import mongo
from . import dashboard_bp

@dashboard_bp.route("/")
@login_required
def home():
    """Main dashboard showing user overview and recent activity"""
    try:
        user_doc = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
        
        # Get recent searches
        recent_searches = list(mongo.db.user_searches.find(
            {"user_id": ObjectId(current_user.id)}
        ).sort("created_at", -1).limit(5))
        
        # Get product details for recent searches
        if recent_searches:
            product_ids = [search["product_id"] for search in recent_searches]
            products = {
                str(p["_id"]): p 
                for p in mongo.db.products.find({"_id": {"$in": product_ids}})
            }
        else:
            products = {}
        
        # Get statistics
        stats = {
            "total_searches": mongo.db.user_searches.count_documents(
                {"user_id": ObjectId(current_user.id)}
            ),
            "total_savings": 0,  # Will be calculated from price histories
            "active_notifications": mongo.db.notifications.count_documents(
                {"user_id": ObjectId(current_user.id), "is_active": True}
            ),
            "registered_cards": len(user_doc.get("cards", []))
        }
        
        # Calculate total savings
        savings_pipeline = [
            {"$match": {"user_id": ObjectId(current_user.id)}},
            {"$group": {
                "_id": None,
                "total_savings": {"$sum": "$total_discount"}
            }}
        ]
        savings_result = list(mongo.db.user_searches.aggregate(savings_pipeline))
        if savings_result:
            stats["total_savings"] = savings_result[0]["total_savings"]
        
        return render_template("dashboard/history.html",
                             user=user_doc,
                             recent_searches=recent_searches,
                             products=products,
                             stats=stats)
        
    except Exception as e:
        logging.error(f"Dashboard error: {e}")
        flash("대시보드를 불러오는 중 오류가 발생했습니다.", "error")
        return redirect(url_for("index"))

@dashboard_bp.route("/analytics")
@login_required
def analytics():
    """Show detailed analytics and trends"""
    try:
        # Get search trends for the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        daily_searches = list(mongo.db.user_searches.aggregate([
            {
                "$match": {
                    "user_id": ObjectId(current_user.id),
                    "created_at": {"$gte": thirty_days_ago}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "count": {"$sum": 1},
                    "total_savings": {"$sum": "$total_discount"}
                }
            },
            {"$sort": {"_id": 1}}
        ]))
        
        # Get top categories
        category_stats = list(mongo.db.user_searches.aggregate([
            {
                "$match": {"user_id": ObjectId(current_user.id)}
            },
            {
                "$lookup": {
                    "from": "products",
                    "localField": "product_id",
                    "foreignField": "_id",
                    "as": "product"
                }
            },
            {"$unwind": "$product"},
            {
                "$group": {
                    "_id": "$product.category",
                    "count": {"$sum": 1},
                    "avg_savings": {"$avg": "$total_discount"}
                }
            },
            {"$sort": {"count": -1}}
        ]))
        
        return render_template("dashboard/analytics.html",
                             daily_searches=daily_searches,
                             category_stats=category_stats)
        
    except Exception as e:
        logging.error(f"Analytics error: {e}")
        flash("분석 데이터를 불러오는 중 오류가 발생했습니다.", "error")
        return redirect(url_for("dashboard.home"))
