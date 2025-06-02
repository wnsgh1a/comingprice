import requests
from bs4 import BeautifulSoup
import re
import logging
from urllib.parse import urljoin, urlparse

def fetch_html(url: str) -> str:
    """Fetch HTML content from URL with error handling"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
        
    except requests.RequestException as e:
        logging.error(f"Failed to fetch URL {url}: {e}")
        return ""

def parse_price(html: str) -> dict:
    """Parse price information from HTML content"""
    if not html:
        return {}
    
    soup = BeautifulSoup(html, "html.parser")
    price_info = {}
    
    try:
        # Try multiple common price selectors
        price_selectors = [
            ".price_original__1yV_U",
            ".price_ins__1mq5M",
            ".price",
            ".sale-price",
            ".current-price",
            ".product-price",
            "[class*='price']",
            "[data-price]"
        ]
        
        # Extract listed price
        for selector in price_selectors:
            price_element = soup.select_one(selector)
            if price_element:
                price_text = price_element.get_text().strip()
                price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
                if price_match:
                    try:
                        price_info["listed_price"] = int(price_match.group().replace(',', ''))
                        break
                    except ValueError:
                        continue
        
        # Try to find sale price
        sale_selectors = [
            ".price_sale__1t_qE",
            ".sale-price",
            ".discounted-price",
            ".special-price",
            "[class*='sale']",
            "[class*='discount']"
        ]
        
        for selector in sale_selectors:
            sale_element = soup.select_one(selector)
            if sale_element:
                sale_text = sale_element.get_text().strip()
                sale_match = re.search(r'[\d,]+', sale_text.replace(',', ''))
                if sale_match:
                    try:
                        price_info["sale_price"] = int(sale_match.group().replace(',', ''))
                        break
                    except ValueError:
                        continue
        
        # Extract product image
        img_selectors = [
            ".product-image img",
            ".main-image img",
            ".hero-image img",
            "img[class*='product']",
            "img[class*='main']"
        ]
        
        for selector in img_selectors:
            img_element = soup.select_one(selector)
            if img_element:
                img_src = img_element.get('src') or img_element.get('data-src')
                if img_src:
                    # Convert relative URLs to absolute
                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    elif img_src.startswith('/'):
                        # Need base URL for this, skip for now
                        pass
                    price_info["image_url"] = img_src
                    break
        
        # Try to extract category
        category_selectors = [
            ".breadcrumb",
            ".category",
            "[class*='category']",
            "[class*='breadcrumb']"
        ]
        
        for selector in category_selectors:
            category_element = soup.select_one(selector)
            if category_element:
                category_text = category_element.get_text().strip()
                if category_text:
                    # Extract last category from breadcrumb
                    categories = [c.strip() for c in category_text.split('>') if c.strip()]
                    if categories:
                        price_info["category"] = categories[-1]
                        break
        
        # Extract product title
        title_selectors = [
            "h1",
            ".product-title",
            ".product-name",
            "[class*='title']",
            "[class*='name']"
        ]
        
        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element:
                title_text = title_element.get_text().strip()
                if title_text:
                    price_info["product_name"] = title_text[:200]  # Limit length
                    break
        
    except Exception as e:
        logging.error(f"Error parsing price from HTML: {e}")
    
    return price_info

def extract_product_details(html: str) -> dict:
    """Extract additional product details from HTML"""
    if not html:
        return {}
    
    soup = BeautifulSoup(html, "html.parser")
    details = {}
    
    try:
        # Extract product description
        desc_selectors = [
            ".product-description",
            ".description",
            "[class*='description']",
            ".product-detail"
        ]
        
        for selector in desc_selectors:
            desc_element = soup.select_one(selector)
            if desc_element:
                desc_text = desc_element.get_text().strip()
                if desc_text:
                    details["description"] = desc_text[:1000]  # Limit length
                    break
        
        # Extract rating if available
        rating_selectors = [
            ".rating",
            ".star-rating",
            "[class*='rating']",
            "[class*='star']"
        ]
        
        for selector in rating_selectors:
            rating_element = soup.select_one(selector)
            if rating_element:
                rating_text = rating_element.get_text().strip()
                rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
                if rating_match:
                    try:
                        details["rating"] = float(rating_match.group(1))
                        break
                    except ValueError:
                        continue
        
        # Extract brand
        brand_selectors = [
            ".brand",
            ".manufacturer",
            "[class*='brand']",
            "[class*='manufacturer']"
        ]
        
        for selector in brand_selectors:
            brand_element = soup.select_one(selector)
            if brand_element:
                brand_text = brand_element.get_text().strip()
                if brand_text:
                    details["brand"] = brand_text
                    break
        
    except Exception as e:
        logging.error(f"Error extracting product details: {e}")
    
    return details
