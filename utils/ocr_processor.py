import io
import requests
import re
import logging
from PIL import Image
import pytesseract
import os

# Set Tesseract path if needed
tesseract_cmd = os.getenv("TESSERACT_CMD", "/usr/bin/tesseract")
if os.path.exists(tesseract_cmd):
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

def ocr_from_image_url(image_url: str) -> str:
    """Extract text from image URL using OCR"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(image_url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
        
        # Open image
        image = Image.open(io.BytesIO(response.content))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Perform OCR with Korean and English
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(image, lang='kor+eng', config=custom_config)
        
        return text.strip()
        
    except Exception as e:
        logging.error(f"OCR processing failed for {image_url}: {e}")
        return ""

def ocr_from_local_image(image_path: str) -> str:
    """Extract text from local image file using OCR"""
    try:
        image = Image.open(image_path)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Perform OCR
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(image, lang='kor+eng', config=custom_config)
        
        return text.strip()
        
    except Exception as e:
        logging.error(f"OCR processing failed for {image_path}: {e}")
        return ""

def extract_discount_info(text: str) -> dict:
    """Extract discount information from OCR text"""
    info = {}
    
    if not text:
        return info
    
    try:
        # Extract percentage discounts (e.g., "10%", "15% 할인")
        percent_patterns = [
            r'(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*퍼센트',
            r'(\d+(?:\.\d+)?)\s*%\s*할인',
            r'(\d+(?:\.\d+)?)\s*%\s*DC'
        ]
        
        for pattern in percent_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Take the highest percentage found
                percentages = [float(match) for match in matches if float(match) <= 100]
                if percentages:
                    info["card_discount"] = max(percentages)
                    break
        
        # Extract fixed amount discounts (e.g., "5000원", "1만원")
        amount_patterns = [
            r'(\d+(?:,\d{3})*)\s*원\s*할인',
            r'(\d+(?:,\d{3})*)\s*원\s*DC',
            r'(\d+(?:,\d{3})*)\s*원\s*쿠폰',
            r'쿠폰\s*(\d+(?:,\d{3})*)\s*원',
            r'(\d+)\s*만\s*원',  # Handle "만원" format
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                amounts = []
                for match in matches:
                    try:
                        if '만' in pattern:
                            # Convert "만원" to actual amount
                            amounts.append(int(match) * 10000)
                        else:
                            amounts.append(int(match.replace(',', '')))
                    except ValueError:
                        continue
                
                if amounts:
                    info["coupon_value"] = max(amounts)
                    break
        
        # Extract cashback information
        cashback_patterns = [
            r'(\d+(?:,\d{3})*)\s*원\s*적립',
            r'적립\s*(\d+(?:,\d{3})*)\s*원',
            r'(\d+(?:\.\d+)?)\s*%\s*적립',
            r'적립\s*(\d+(?:\.\d+)?)\s*%'
        ]
        
        for pattern in cashback_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    if '%' in pattern:
                        cashback_rates = [float(match) for match in matches if float(match) <= 100]
                        if cashback_rates:
                            info["cashback_rate"] = max(cashback_rates)
                    else:
                        cashback_amounts = [int(match.replace(',', '')) for match in matches]
                        if cashback_amounts:
                            info["cashback_amount"] = max(cashback_amounts)
                    break
                except ValueError:
                    continue
        
        # Extract card-specific discounts
        card_patterns = [
            r'(신한|삼성|현대|KB|우리|하나|농협|IBK|SC제일|씨티)\s*카드?\s*(\d+(?:\.\d+)?)\s*%',
            r'(신한|삼성|현대|KB|우리|하나|농협|IBK|SC제일|씨티)\s*(\d+(?:,\d{3})*)\s*원'
        ]
        
        card_discounts = {}
        for pattern in card_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for card_name, discount in matches:
                try:
                    if '%' in pattern:
                        card_discounts[card_name] = {"type": "percentage", "value": float(discount)}
                    else:
                        card_discounts[card_name] = {"type": "fixed", "value": int(discount.replace(',', ''))}
                except ValueError:
                    continue
        
        if card_discounts:
            info["card_specific_discounts"] = card_discounts
        
        # Extract minimum purchase amount
        min_purchase_patterns = [
            r'(\d+(?:,\d{3})*)\s*원\s*이상',
            r'최소\s*(\d+(?:,\d{3})*)\s*원',
            r'(\d+)\s*만\s*원\s*이상'
        ]
        
        for pattern in min_purchase_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    if '만' in pattern:
                        info["min_purchase"] = int(matches[0]) * 10000
                    else:
                        info["min_purchase"] = int(matches[0].replace(',', ''))
                    break
                except ValueError:
                    continue
        
    except Exception as e:
        logging.error(f"Error extracting discount info from text: {e}")
    
    return info

def preprocess_image(image):
    """Preprocess image for better OCR results"""
    try:
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # You can add more preprocessing steps here:
        # - Noise reduction
        # - Contrast enhancement
        # - Deskewing
        # - Resizing
        
        return image
    except Exception as e:
        logging.error(f"Image preprocessing failed: {e}")
        return image

def extract_text_regions(image):
    """Extract specific text regions from image"""
    # This could be enhanced with computer vision techniques
    # to identify and extract specific regions like price tags,
    # discount badges, etc.
    return []
