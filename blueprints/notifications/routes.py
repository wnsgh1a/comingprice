from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from bson.objectid import ObjectId
from datetime import datetime
import logging
from db import mongo
from utils.email_notifier import send_price_alert
from . import notifications_bp

@notifications_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """Manage notification settings and price alerts"""
    if request.method == "POST":
        try:
            action = request.form.get("action")
            
            if action == "add_alert":
                product_id = request.form.get("product_id")
                target_price = request.form.get("target_price")
                
                if not product_id or not target_price:
                    flash("상품과 목표 가격을 선택해주세요.", "error")
                    return redirect(url_for("notifications.settings"))
                
                try:
                    target_price = int(target_price)
                    product_id = ObjectId(product_id)
                except (ValueError, TypeError):
                    flash("올바른 가격을 입력해주세요.", "error")
                    return redirect(url_for("notifications.settings"))
                
                # Check if notification already exists
                existing = mongo.db.notifications.find_one({
                    "user_id": ObjectId(current_user.id),
                    "product_id": product_id,
                    "is_active": True
                })
                
                if existing:
                    flash("이미 해당 상품에 대한 알림이 설정되어 있습니다.", "warning")
                else:
                    notification_doc = {
                        "user_id": ObjectId(current_user.id),
                        "product_id": product_id,
                        "target_price": target_price,
                        "is_active": True,
                        "created_at": datetime.utcnow(),
                        "triggered_at": None
                    }
                    
                    mongo.db.notifications.insert_one(notification_doc)
                    flash("가격 알림이 설정되었습니다.", "success")
            
            elif action == "toggle_notification":
                notification_id = request.form.get("notification_id")
                is_active = request.form.get("is_active") == "true"
                
                mongo.db.notifications.update_one(
                    {
                        "_id": ObjectId(notification_id),
                        "user_id": ObjectId(current_user.id)
                    },
                    {"$set": {"is_active": is_active}}
                )
                
                status = "활성화" if is_active else "비활성화"
                flash(f"알림이 {status}되었습니다.", "success")
            
            elif action == "delete_notification":
                notification_id = request.form.get("notification_id")
                
                result = mongo.db.notifications.delete_one({
                    "_id": ObjectId(notification_id),
                    "user_id": ObjectId(current_user.id)
                })
                
                if result.deleted_count > 0:
                    flash("알림이 삭제되었습니다.", "success")
                else:
                    flash("알림 삭제에 실패했습니다.", "error")
            
            elif action == "update_settings":
                email_enabled = request.form.get("email_enabled") == "on"
                price_alerts = request.form.get("price_alerts") == "on"
                
                mongo.db.users.update_one(
                    {"_id": ObjectId(current_user.id)},
                    {"$set": {
                        "notification_settings.email_enabled": email_enabled,
                        "notification_settings.price_alerts": price_alerts
                    }}
                )
                flash("알림 설정이 업데이트되었습니다.", "success")
            
        except Exception as e:
            logging.error(f"Notification settings error: {e}")
            flash("설정 처리 중 오류가 발생했습니다.", "error")
        
        return redirect(url_for("notifications.settings"))
    
    try:
        # Get user's notifications
        notifications = list(mongo.db.notifications.find(
            {"user_id": ObjectId(current_user.id)}
        ).sort("created_at", -1))
        
        # Get products for notifications
        if notifications:
            product_ids = [notif["product_id"] for notif in notifications]
            products = {
                str(p["_id"]): p 
                for p in mongo.db.products.find({"_id": {"$in": product_ids}})
            }
        else:
            products = {}
        
        # Get user's recent searches for adding new alerts
        recent_searches = list(mongo.db.user_searches.find(
            {"user_id": ObjectId(current_user.id)}
        ).sort("created_at", -1).limit(10))
        
        if recent_searches:
            search_product_ids = [search["product_id"] for search in recent_searches]
            search_products = list(mongo.db.products.find(
                {"_id": {"$in": search_product_ids}}
            ))
        else:
            search_products = []
        
        # Get user settings
        user_doc = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
        
        return render_template("notifications/settings.html",
                             notifications=notifications,
                             products=products,
                             search_products=search_products,
                             user=user_doc)
        
    except Exception as e:
        logging.error(f"Notification settings page error: {e}")
        flash("알림 설정을 불러오는 중 오류가 발생했습니다.", "error")
        return redirect(url_for("dashboard.home"))

@notifications_bp.route("/check_prices")
@login_required
def check_prices():
    """Manual price check for user's notifications"""
    try:
        # This would typically be run by a background job
        # For demo purposes, we'll show it as a manual action
        
        notifications = list(mongo.db.notifications.find({
            "user_id": ObjectId(current_user.id),
            "is_active": True
        }))
        
        alerts_triggered = 0
        
        for notification in notifications:
            # Get latest price for the product
            product = mongo.db.products.find_one({"_id": notification["product_id"]})
            
            if product and product.get("price_histories"):
                latest_price = product["price_histories"][-1]["computed_price"]
                
                if latest_price <= notification["target_price"]:
                    # Trigger alert
                    user_doc = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
                    
                    if user_doc.get("notification_settings", {}).get("email_enabled", True):
                        send_price_alert(user_doc["email"], product, latest_price, notification["target_price"])
                    
                    # Mark notification as triggered
                    mongo.db.notifications.update_one(
                        {"_id": notification["_id"]},
                        {"$set": {"triggered_at": datetime.utcnow()}}
                    )
                    
                    alerts_triggered += 1
        
        if alerts_triggered > 0:
            flash(f"{alerts_triggered}개의 가격 알림이 발송되었습니다.", "success")
        else:
            flash("현재 목표 가격에 도달한 상품이 없습니다.", "info")
        
    except Exception as e:
        logging.error(f"Price check error: {e}")
        flash("가격 확인 중 오류가 발생했습니다.", "error")
    
    return redirect(url_for("notifications.settings"))
