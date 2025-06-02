from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, UserMixin
from bson.objectid import ObjectId
from datetime import datetime
import logging
from db import mongo
from . import auth_bp

class MongoUser(UserMixin):
    """User class for Flask-Login"""
    def __init__(self, doc):
        self.id = str(doc["_id"])
        self.username = doc["username"]
        self.email = doc["email"]
        self.cards = doc.get("cards", [])
        self.created_at = doc.get("created_at")

def user_loader(user_id):
    """Load user by ID for Flask-Login"""
    try:
        doc = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        return MongoUser(doc) if doc else None
    except Exception as e:
        logging.error(f"Error loading user {user_id}: {e}")
        return None

# Register user loader with login manager
from app import login_manager
login_manager.user_loader(user_loader)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        
        if not email or not password:
            flash("이메일과 비밀번호를 입력해주세요.", "error")
            return render_template("auth/login.html")
        
        try:
            user_doc = mongo.db.users.find_one({"email": email})
            if user_doc and check_password_hash(user_doc["password_hash"], password):
                user = MongoUser(user_doc)
                login_user(user, remember=True)
                flash(f"안녕하세요, {user.username}님!", "success")
                next_page = request.args.get('next')
                return redirect(next_page or url_for("dashboard.home"))
            else:
                flash("이메일 또는 비밀번호가 올바르지 않습니다.", "error")
        except Exception as e:
            logging.error(f"Login error: {e}")
            flash("로그인 중 오류가 발생했습니다.", "error")
    
    return render_template("auth/login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash("모든 필드를 입력해주세요.", "error")
            return render_template("auth/register.html")
        
        if password != confirm_password:
            flash("비밀번호가 일치하지 않습니다.", "error")
            return render_template("auth/register.html")
        
        if len(password) < 6:
            flash("비밀번호는 최소 6자 이상이어야 합니다.", "error")
            return render_template("auth/register.html")
        
        try:
            # Check if user already exists
            if mongo.db.users.find_one({"email": email}):
                flash("이미 가입된 이메일입니다.", "error")
                return render_template("auth/register.html")
            
            if mongo.db.users.find_one({"username": username}):
                flash("이미 사용중인 사용자명입니다.", "error")
                return render_template("auth/register.html")
            
            # Create new user
            password_hash = generate_password_hash(password)
            user_doc = {
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "cards": [],
                "notification_settings": {
                    "email_enabled": True,
                    "price_alerts": True
                },
                "created_at": datetime.utcnow()
            }
            
            result = mongo.db.users.insert_one(user_doc)
            if result.inserted_id:
                flash("회원가입이 완료되었습니다! 로그인해주세요.", "success")
                return redirect(url_for("auth.login"))
            else:
                flash("회원가입 중 오류가 발생했습니다.", "error")
                
        except Exception as e:
            logging.error(f"Registration error: {e}")
            flash("회원가입 중 오류가 발생했습니다.", "error")
    
    return render_template("auth/register.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("로그아웃되었습니다.", "info")
    return redirect(url_for("index"))

@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    from flask_login import current_user
    
    if request.method == "POST":
        try:
            # Update user cards
            cards = []
            card_names = request.form.getlist("card_name[]")
            card_rates = request.form.getlist("card_rate[]")
            
            for name, rate in zip(card_names, card_rates):
                if name.strip() and rate.strip():
                    try:
                        cards.append({
                            "name": name.strip(),
                            "discount_rate": float(rate),
                            "added_at": datetime.utcnow()
                        })
                    except ValueError:
                        flash(f"카드 '{name}'의 할인율이 올바르지 않습니다.", "error")
                        continue
            
            # Update user document
            mongo.db.users.update_one(
                {"_id": ObjectId(current_user.id)},
                {"$set": {"cards": cards}}
            )
            flash("프로필이 업데이트되었습니다.", "success")
            
        except Exception as e:
            logging.error(f"Profile update error: {e}")
            flash("프로필 업데이트 중 오류가 발생했습니다.", "error")
    
    # Get updated user data
    user_doc = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
    return render_template("auth/profile.html", user=user_doc)
