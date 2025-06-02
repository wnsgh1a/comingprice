import logging
from typing import List, Dict, Any, Optional

def compute_final_price(scraped_price: int, ocr_info: Dict, user_cards: List[Dict]) -> Dict:
    """
    Compute the final price after applying all available discounts
    
    Args:
        scraped_price: Base price from website scraping
        ocr_info: Discount information extracted from OCR
        user_cards: List of user's credit cards with discount rates
        
    Returns:
        Dictionary with final price and discount breakdown
    """
    try:
        result = {
            "original_price": scraped_price,
            "final_price": scraped_price,
            "total_discount": 0,
            "discount_breakdown": [],
            "best_card": None,
            "recommended_payment": None
        }
        
        current_price = scraped_price
        
        # Apply OCR-detected percentage discount first
        if ocr_info.get("card_discount"):
            discount_rate = ocr_info["card_discount"]
            discount_amount = int(current_price * discount_rate / 100)
            current_price -= discount_amount
            
            result["discount_breakdown"].append({
                "type": "percentage_discount",
                "description": f"상품 할인 {discount_rate}%",
                "amount": discount_amount
            })
        
        # Apply OCR-detected fixed coupon discount
        if ocr_info.get("coupon_value"):
            coupon_discount = min(ocr_info["coupon_value"], current_price)
            current_price -= coupon_discount
            
            result["discount_breakdown"].append({
                "type": "coupon_discount",
                "description": f"쿠폰 할인",
                "amount": coupon_discount
            })
        
        # Check minimum purchase requirement
        min_purchase = ocr_info.get("min_purchase", 0)
        if min_purchase > 0 and scraped_price < min_purchase:
            result["warnings"] = [f"최소 구매 금액 {min_purchase:,}원 미달"]
        
        # Calculate best card discount
        best_card_discount = 0
        best_card = None
        
        for card in user_cards:
            if not card.get("discount_rate"):
                continue
                
            card_discount_rate = card["discount_rate"]
            card_discount_amount = int(current_price * card_discount_rate / 100)
            
            # Apply card-specific limits if any
            max_discount = card.get("max_discount_amount")
            if max_discount and card_discount_amount > max_discount:
                card_discount_amount = max_discount
            
            if card_discount_amount > best_card_discount:
                best_card_discount = card_discount_amount
                best_card = card
        
        # Apply best card discount
        if best_card_discount > 0:
            current_price -= best_card_discount
            result["best_card"] = best_card
            result["discount_breakdown"].append({
                "type": "card_discount",
                "description": f"{best_card['name']} 카드 할인 {best_card['discount_rate']}%",
                "amount": best_card_discount
            })
        
        # Check for card-specific discounts from OCR
        if ocr_info.get("card_specific_discounts"):
            card_specific = ocr_info["card_specific_discounts"]
            
            # Find if user has any of the cards mentioned in OCR
            for user_card in user_cards:
                card_name = user_card["name"]
                
                # Simple matching - could be improved with fuzzy matching
                for ocr_card_name, discount_info in card_specific.items():
                    if ocr_card_name in card_name or card_name in ocr_card_name:
                        if discount_info["type"] == "percentage":
                            additional_discount = int(current_price * discount_info["value"] / 100)
                        else:
                            additional_discount = min(discount_info["value"], current_price)
                        
                        # Only apply if it's better than the generic card discount
                        if additional_discount > best_card_discount:
                            # Remove previous card discount
                            if best_card_discount > 0:
                                current_price += best_card_discount
                                result["discount_breakdown"] = [
                                    d for d in result["discount_breakdown"] 
                                    if d["type"] != "card_discount"
                                ]
                            
                            # Apply specific card discount
                            current_price -= additional_discount
                            result["best_card"] = user_card
                            result["discount_breakdown"].append({
                                "type": "card_specific_discount",
                                "description": f"{card_name} 특별 할인",
                                "amount": additional_discount
                            })
                            break
        
        # Apply cashback if available (this doesn't reduce current price but adds value)
        cashback_amount = 0
        if ocr_info.get("cashback_rate"):
            cashback_amount = int(current_price * ocr_info["cashback_rate"] / 100)
        elif ocr_info.get("cashback_amount"):
            cashback_amount = ocr_info["cashback_amount"]
        
        if cashback_amount > 0:
            result["discount_breakdown"].append({
                "type": "cashback",
                "description": f"적립금",
                "amount": cashback_amount
            })
        
        # Calculate totals
        result["final_price"] = max(0, current_price)  # Ensure non-negative
        result["total_discount"] = scraped_price - result["final_price"]
        result["cashback_amount"] = cashback_amount
        result["effective_price"] = result["final_price"] - cashback_amount
        
        # Generate payment recommendation
        result["recommended_payment"] = generate_payment_recommendation(result, ocr_info)
        
        return result
        
    except Exception as e:
        logging.error(f"Error computing final price: {e}")
        return {
            "original_price": scraped_price,
            "final_price": scraped_price,
            "total_discount": 0,
            "discount_breakdown": [],
            "error": str(e)
        }

def generate_payment_recommendation(price_result: Dict, ocr_info: Dict) -> str:
    """Generate a payment recommendation based on the discount analysis"""
    try:
        recommendations = []
        
        if price_result.get("best_card"):
            card_name = price_result["best_card"]["name"]
            recommendations.append(f"{card_name} 카드 사용 권장")
        
        if price_result.get("cashback_amount", 0) > 0:
            recommendations.append(f"적립금 {price_result['cashback_amount']:,}원 예상")
        
        total_savings = price_result.get("total_discount", 0)
        cashback = price_result.get("cashback_amount", 0)
        
        if total_savings > 0 or cashback > 0:
            total_benefit = total_savings + cashback
            savings_rate = (total_benefit / price_result["original_price"]) * 100
            recommendations.append(f"총 {total_benefit:,}원 절약 ({savings_rate:.1f}%)")
        
        # Check for warnings
        if ocr_info.get("min_purchase"):
            min_amount = ocr_info["min_purchase"]
            if price_result["original_price"] < min_amount:
                recommendations.append(f"⚠️ 최소 구매금액 {min_amount:,}원 확인 필요")
        
        return " | ".join(recommendations) if recommendations else "추가 할인 혜택 없음"
        
    except Exception as e:
        logging.error(f"Error generating payment recommendation: {e}")
        return "할인 정보 분석 중 오류 발생"

def compare_payment_options(scraped_price: int, ocr_info: Dict, user_cards: List[Dict]) -> List[Dict]:
    """Compare different payment options and return sorted by best value"""
    try:
        options = []
        
        # Option 1: No card (base price with available discounts)
        base_result = compute_final_price(scraped_price, ocr_info, [])
        options.append({
            "method": "현금/체크카드",
            "final_price": base_result["final_price"],
            "total_savings": base_result["total_discount"],
            "description": "기본 할인만 적용"
        })
        
        # Option 2: Each user card
        for card in user_cards:
            card_result = compute_final_price(scraped_price, ocr_info, [card])
            options.append({
                "method": f"{card['name']} 카드",
                "final_price": card_result["final_price"],
                "total_savings": card_result["total_discount"],
                "cashback": card_result.get("cashback_amount", 0),
                "description": f"{card['discount_rate']}% 할인"
            })
        
        # Option 3: Best combination
        best_result = compute_final_price(scraped_price, ocr_info, user_cards)
        if best_result.get("best_card"):
            options.append({
                "method": "최적 조합",
                "final_price": best_result["final_price"],
                "total_savings": best_result["total_discount"],
                "cashback": best_result.get("cashback_amount", 0),
                "description": best_result["recommended_payment"]
            })
        
        # Sort by effective price (final price minus cashback)
        options.sort(key=lambda x: x["final_price"] - x.get("cashback", 0))
        
        return options
        
    except Exception as e:
        logging.error(f"Error comparing payment options: {e}")
        return []

def calculate_savings_potential(products: List[Dict], user_cards: List[Dict]) -> Dict:
    """Calculate potential savings across multiple products"""
    try:
        total_original = 0
        total_final = 0
        total_savings = 0
        best_cards = {}
        
        for product in products:
            if not product.get("price_histories"):
                continue
                
            latest_price = product["price_histories"][-1]
            original_price = latest_price.get("scraped_price", 0)
            
            # Simulate discount calculation
            result = compute_final_price(original_price, {}, user_cards)
            
            total_original += original_price
            total_final += result["final_price"]
            total_savings += result["total_discount"]
            
            if result.get("best_card"):
                card_name = result["best_card"]["name"]
                best_cards[card_name] = best_cards.get(card_name, 0) + 1
        
        return {
            "total_original_price": total_original,
            "total_final_price": total_final,
            "total_savings": total_savings,
            "savings_rate": (total_savings / total_original * 100) if total_original > 0 else 0,
            "most_used_card": max(best_cards.items(), key=lambda x: x[1])[0] if best_cards else None,
            "products_analyzed": len(products)
        }
        
    except Exception as e:
        logging.error(f"Error calculating savings potential: {e}")
        return {}
