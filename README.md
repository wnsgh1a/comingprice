Coming Price 📈

가격 변동을 한눈에 — 상품 할인 모니터링 & 자동 알림 플랫폼

Coming Price는 온라인 쇼핑몰과 전단지 데이터를 실시간으로 수집·분석하여 최적의 구매 시점을 알려주는 오픈소스 프로젝트입니다. Flask 기반 백엔드와 MongoDB를 사용해 크롤링·OCR·알림 엔진을 모듈화했으며, 누구나 손쉽게 로컬/클라우드에 배포해 활용할 수 있습니다.

✨ 주요 기능

카테고리

설명

가격 크롤링

Selenium & Requests로 다중 쇼핑몰 가격·재고 정보 수집

OCR 분석

Google Vision API로 전단지/영수증 텍스트 추출 및 구조화

할인 계산

과거 데이터와 비교해 할인율·트렌드 시각화

알림 서비스

이메일·웹훅·푸시(FCM)로 실시간 특가 알림

대시보드

Jinja2 + Chart.js 기반 웹 UI로 손쉽게 확인

🛠️ 기술 스택

Backend : Python 3.12, Flask 3.x, PyMongo

DB      : MongoDB 7 (도커 컨테이너 권장)

Frontend: HTML + Jinja2 템플릿, Bootstrap 5, Chart.js

Other   : python-dotenv, Gunicorn, uv (패키지 관리자)

🚀 빠른 시작

1) 저장소 클론 & 이동

git clone https://github.com/wnsgh1a/comingprice.git
cd comingprice

2) 가상환경·의존성 설치

python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install --upgrade uv
uv pip install -r uv.lock   # 또는 uv pip install -e .

3) .env 파일 생성

.env.example 를 참고해 아래와 같이 작성합니다.

SECRET_KEY=changeme
MONGODB_URI=mongodb://localhost:27017/comingprice
MAIL_USERNAME=your@email.com
MAIL_PASSWORD=********

4) 데이터베이스 기동 (도커 예시)

docker run -d -p 27017:27017 --name mongo mongo:7

5) 개발 서버 실행

flask --app app:create_app --debug run  # http://localhost:5000/

📂 프로젝트 구조

comingprice/
├── app.py               # Flask 앱 팩토리
├── config.py            # 설정 로더 (env 기반)
├── db.py                # PyMongo 헬퍼
├── blueprints/          # auth / products / dashboard / notifications
├── utils/               # crawler, ocr_processor, discount_engine 등
├── templates/           # Jinja2 템플릿
├── static/              # 정적 자산 (CSS/JS)
├── pyproject.toml       # PEP 517/518 메타 & 의존성
├── uv.lock              # 잠금파일
└── README.md | LICENSE  # 문서

🤝 기여 가이드

이슈 등록 → 포크 ↔ PR 순으로 진행해 주세요.

새 기능은 단위 테스트를 포함해야 합니다.

PR 제목은 [feat] … [fix] … [docs] … 형식을 따릅니다.

코드 스타일은 PEP 8 & black 포맷터를 기준으로 합니다.

📝 라이선스

본 프로젝트는 MIT 라이선스로 배포됩니다. 자세한 내용은 LICENSE 파일을 확인하세요.

📧 문의

Author : 준호 최 (https://github.com/wnsgh1a)

Issue  : https://github.com/wnsgh1a/comingprice/issues

즐겁게 활용해 주세요! 🎉

