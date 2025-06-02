import logging
from flask_mail import Message
from flask import current_app, render_template_string
from datetime import datetime

def send_price_alert(user_email: str, product: dict, current_price: int, target_price: int) -> bool:
    """Send price alert email to user"""
    try:
        from app import mail
        
        subject = f"🎯 가격 알림: {product.get('name', 'Unknown Product')} 목표 가격 도달!"
        
        # Email template
        email_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #007bff; color: white; padding: 20px; border-radius: 8px 8px 0 0; }
                .content { background: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; }
                .price-alert { background: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 15px 0; }
                .price { font-size: 24px; font-weight: bold; color: #28a745; }
                .target-price { font-size: 18px; color: #6c757d; }
                .product-info { background: white; border-radius: 5px; padding: 15px; margin: 15px 0; }
                .button { display: inline-block; background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 가격 알림</h1>
                    <p>설정하신 목표 가격에 도달했습니다!</p>
                </div>
                <div class="content">
                    <div class="price-alert">
                        <h2>{{ product_name }}</h2>
                        <div class="price">현재 가격: {{ "{:,}".format(current_price) }}원</div>
                        <div class="target-price">목표 가격: {{ "{:,}".format(target_price) }}원</div>
                        <p><strong>{{ "{:,}".format(target_price - current_price) }}원 더 저렴해졌습니다!</strong></p>
                    </div>
                    
                    <div class="product-info">
                        <h3>상품 정보</h3>
                        <p><strong>상품명:</strong> {{ product_name }}</p>
                        <p><strong>확인 시각:</strong> {{ check_time }}</p>
                        {% if product_url %}
                        <p><a href="{{ product_url }}" class="button">상품 보러가기</a></p>
                        {% endif %}
                    </div>
                    
                    <div style="margin-top: 30px; font-size: 12px; color: #6c757d;">
                        <p>이 알림은 ComImg 가격 비교 서비스에서 발송되었습니다.</p>
                        <p>더 이상 알림을 받고 싶지 않으시면 알림 설정에서 비활성화할 수 있습니다.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        html_body = render_template_string(email_template,
            product_name=product.get('name', 'Unknown Product'),
            current_price=current_price,
            target_price=target_price,
            product_url=product.get('url'),
            check_time=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # Plain text version
        text_body = f"""
가격 알림: {product.get('name', 'Unknown Product')}

목표 가격에 도달했습니다!

현재 가격: {current_price:,}원
목표 가격: {target_price:,}원
절약 금액: {target_price - current_price:,}원

상품 URL: {product.get('url', 'N/A')}
확인 시각: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

ComImg 가격 비교 서비스
        """
        
        msg = Message(
            subject=subject,
            recipients=[user_email],
            html=html_body,
            body=text_body
        )
        
        mail.send(msg)
        logging.info(f"Price alert email sent to {user_email} for product {product.get('name')}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send price alert email: {e}")
        return False

def send_welcome_email(user_email: str, username: str) -> bool:
    """Send welcome email to new users"""
    try:
        from app import mail
        
        subject = "ComImg에 오신 것을 환영합니다! 🎉"
        
        welcome_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #28a745; color: white; padding: 20px; border-radius: 8px 8px 0 0; }
                .content { background: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; }
                .feature { background: white; border-radius: 5px; padding: 15px; margin: 10px 0; }
                .button { display: inline-block; background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>환영합니다, {{ username }}님! 🎉</h1>
                    <p>ComImg 가격 비교 서비스에 가입해주셔서 감사합니다.</p>
                </div>
                <div class="content">
                    <h2>ComImg로 할 수 있는 것들:</h2>
                    
                    <div class="feature">
                        <h3>🔍 똑똑한 가격 비교</h3>
                        <p>상품 URL만 입력하면 실시간 가격을 분석하고 최저가를 찾아드립니다.</p>
                    </div>
                    
                    <div class="feature">
                        <h3>💳 카드 할인 최적화</h3>
                        <p>보유하신 신용카드 정보를 등록하면 가장 유리한 결제 방법을 추천해드립니다.</p>
                    </div>
                    
                    <div class="feature">
                        <h3>🔔 가격 알림</h3>
                        <p>원하는 가격에 도달하면 즉시 알림을 받아보세요.</p>
                    </div>
                    
                    <div class="feature">
                        <h3>📊 할인 정보 OCR</h3>
                        <p>상품 이미지에서 할인 정보를 자동으로 인식하여 정확한 가격을 계산합니다.</p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="#" class="button">지금 시작하기</a>
                    </div>
                    
                    <div style="margin-top: 30px; font-size: 12px; color: #6c757d;">
                        <p>질문이나 문의사항이 있으시면 언제든 연락주세요.</p>
                        <p>ComImg 팀 드림</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        html_body = render_template_string(welcome_template, username=username)
        
        text_body = f"""
환영합니다, {username}님!

ComImg 가격 비교 서비스에 가입해주셔서 감사합니다.

ComImg의 주요 기능:
- 똑똑한 가격 비교: 상품 URL로 실시간 최저가 검색
- 카드 할인 최적화: 보유 카드별 최적 결제 방법 추천
- 가격 알림: 목표 가격 도달 시 즉시 알림
- 할인 정보 OCR: 이미지에서 할인 정보 자동 인식

지금 바로 시작해보세요!

ComImg 팀 드림
        """
        
        msg = Message(
            subject=subject,
            recipients=[user_email],
            html=html_body,
            body=text_body
        )
        
        mail.send(msg)
        logging.info(f"Welcome email sent to {user_email}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send welcome email: {e}")
        return False

def send_weekly_summary(user_email: str, username: str, summary_data: dict) -> bool:
    """Send weekly summary email with savings and recommendations"""
    try:
        from app import mail
        
        subject = f"📊 {username}님의 주간 절약 리포트"
        
        summary_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #6f42c1; color: white; padding: 20px; border-radius: 8px 8px 0 0; }
                .content { background: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; }
                .stat-box { background: white; border-radius: 5px; padding: 15px; margin: 10px 0; text-align: center; }
                .stat-number { font-size: 32px; font-weight: bold; color: #28a745; }
                .stat-label { font-size: 14px; color: #6c757d; }
                .recommendation { background: #e3f2fd; border-left: 4px solid #2196f3; padding: 15px; margin: 15px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 주간 절약 리포트</h1>
                    <p>{{ username }}님의 지난 주 활동 요약입니다.</p>
                </div>
                <div class="content">
                    <div class="stat-box">
                        <div class="stat-number">{{ "{:,}".format(total_savings) }}원</div>
                        <div class="stat-label">이번 주 총 절약 금액</div>
                    </div>
                    
                    <div class="stat-box">
                        <div class="stat-number">{{ searches_count }}</div>
                        <div class="stat-label">상품 검색 횟수</div>
                    </div>
                    
                    <div class="stat-box">
                        <div class="stat-number">{{ alerts_triggered }}</div>
                        <div class="stat-label">가격 알림 발생</div>
                    </div>
                    
                    {% if best_card %}
                    <div class="recommendation">
                        <h3>💳 이번 주 최고 혜택 카드</h3>
                        <p><strong>{{ best_card }}</strong>가 가장 많은 절약을 도와드렸습니다!</p>
                    </div>
                    {% endif %}
                    
                    {% if recommendations %}
                    <div class="recommendation">
                        <h3>📈 다음 주 추천</h3>
                        <ul>
                        {% for rec in recommendations %}
                            <li>{{ rec }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                    {% endif %}
                    
                    <div style="margin-top: 30px; font-size: 12px; color: #6c757d;">
                        <p>계속해서 더 많은 절약을 위해 ComImg를 활용해보세요!</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        html_body = render_template_string(summary_template,
            username=username,
            total_savings=summary_data.get('total_savings', 0),
            searches_count=summary_data.get('searches_count', 0),
            alerts_triggered=summary_data.get('alerts_triggered', 0),
            best_card=summary_data.get('best_card'),
            recommendations=summary_data.get('recommendations', [])
        )
        
        msg = Message(
            subject=subject,
            recipients=[user_email],
            html=html_body
        )
        
        mail.send(msg)
        logging.info(f"Weekly summary email sent to {user_email}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send weekly summary email: {e}")
        return False
