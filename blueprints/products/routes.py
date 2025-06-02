from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from bson import ObjectId
from datetime import datetime
import logging
from db import mongo
from utils.crawler import fetch_html, parse_price
from utils.ocr_processor import ocr_from_image_url, extract_discount_info
from utils.discount_engine import compute_final_price
from . import products_bp

@products_bp.route("/search", methods=["GET"])
@login_required
def search_form():
    """Display product search form"""
    return render_template("products/search.html")

@products_bp.route("/search", methods=["POST"])
@login_required
def search_action():
    """Process product search and price analysis"""
    try:
        url = request.form.get("product_url", "").strip()
        product_name = request.form.get("product_name", "").strip()
        
        if not url:
            flash("상품 URL을 입력해주세요.", "error")
            return redirect(url_for("products.search_form"))
        
        # Fetch and parse HTML
        html = fetch_html(url)
        if not html:
            flash("상품 페이지를 불러올 수 없습니다.", "error")
            return redirect(url_for("products.search_form"))
        
        price_info = parse_price(html)
        if not price_info.get("listed_price"):
            flash("상품 가격을 찾을 수 없습니다.", "error")
            return redirect(url_for("products.search_form"))
        
        # OCR processing for discount information
        ocr_text = ""
        discount_data = {}
        
        if price_info.get("image_url"):
            try:
                ocr_text = ocr_from_image_url(price_info["image_url"])
                discount_data = extract_discount_info(ocr_text)
            except Exception as e:
                logging.warning(f"OCR processing failed: {e}")
        
        # Get user cards for discount calculation
        user_doc = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
        user_cards = user_doc.get("cards", [])
        
        # Calculate final price with discounts
        base_price = price_info.get("sale_price") or price_info["listed_price"]
        final_result = compute_final_price(base_price, discount_data, user_cards)
        
        # Save/update product in database
        product_data = {
            "name": product_name or f"Product from {url}",
            "url": url,
            "image_url": price_info.get("image_url"),
            "category": price_info.get("category", "기타"),
            "updated_at": datetime.utcnow()
        }
        
        # Price history entry
        price_history_entry = {
            "scraped_price": price_info.get("sale_price") or price_info["listed_price"],
            "listed_price": price_info["listed_price"],
            "ocr_discount": discount_data.get("card_discount", 0),
            "ocr_coupon": discount_data.get("coupon_value", 0),
            "computed_price": final_result["final_price"],
            "best_card": final_result.get("best_card"),
            "total_discount": final_result.get("total_discount", 0),
            "currency": "KRW",
            "user_id": ObjectId(current_user.id),
            "created_at": datetime.utcnow()
        }
        
        # Upsert product
        product = mongo.db.products.find_one_and_update(
            {"url": url},
            {
                "$setOnInsert": {
                    **product_data,
                    "created_at": datetime.utcnow()
                },
                "$set": product_data,
                "$push": {
                    "price_histories": price_history_entry
                }
            },
            upsert=True,
            return_document=True
        )
        
        # Add to user's search history
        mongo.db.user_searches.insert_one({
            "user_id": ObjectId(current_user.id),
            "product_id": product["_id"],
            "search_url": url,
            "result_price": final_result["final_price"],
            "created_at": datetime.utcnow()
        })
        
        return render_template("products/result.html",
                             product=product,
                             price_info=price_info,
                             discount_data=discount_data,
                             final_result=final_result,
                             ocr_text=ocr_text)
        
    except Exception as e:
        logging.error(f"Product search error: {e}")
        flash("상품 검색 중 오류가 발생했습니다.", "error")
        return redirect(url_for("products.search_form"))

@products_bp.route("/history")
@login_required
def search_history():
    """Display user's search history"""
    try:
        # Get user's recent searches
        searches = list(mongo.db.user_searches.find(
            {"user_id": ObjectId(current_user.id)}
        ).sort("created_at", -1).limit(20))
        
        # Get product details for each search
        product_ids = [search["product_id"] for search in searches]
        products = {
            str(p["_id"]): p 
            for p in mongo.db.products.find({"_id": {"$in": product_ids}})
        }
        
        return render_template("products/history.html",
                             searches=searches,
                             products=products)
        
    except Exception as e:
        logging.error(f"Search history error: {e}")
        flash("검색 기록을 불러오는 중 오류가 발생했습니다.", "error")
        return redirect(url_for("dashboard.home"))

@products_bp.route("/compare")
@login_required
def compare_products():
    """Compare multiple products"""
    try:
        # Get user's recent unique products
        recent_searches = list(mongo.db.user_searches.find(
            {"user_id": ObjectId(current_user.id)}
        ).sort("created_at", -1).limit(50))
        
        # Get unique products
        seen_products = set()
        unique_searches = []
        for search in recent_searches:
            if search["product_id"] not in seen_products:
                unique_searches.append(search)
                seen_products.add(search["product_id"])
                if len(unique_searches) >= 10:
                    break
        
        # Get product details
        product_ids = [search["product_id"] for search in unique_searches]
        products = list(mongo.db.products.find({"_id": {"$in": product_ids}}))
        
        return render_template("products/compare.html",
                             products=products,
                             searches=unique_searches)
        
    except Exception as e:
        logging.error(f"Product comparison error: {e}")
        flash("상품 비교 중 오류가 발생했습니다.", "error")
        return redirect(url_for("dashboard.home"))
