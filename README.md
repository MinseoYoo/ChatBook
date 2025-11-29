# ChatBook (SQUIN Book Agent)

문헌정보학과에서 배운 독자상담방법론을 기반으로 도서 추천을 수행하는 에이전트를 만들었어요. Docker와 AWS EC2를 통한 AI 서비스 배포 또한 연습하고 싶었고, 본전공인 문헌정보학을 프롬프트에 녹여보고 싶은 흥미에 시작한 작은 프로젝트입니다😆

## ✨ 주요 기능

### 1. 면담형 인터페이스
- 8단계 질문을 통해 사용자의 독서 경험과 도서에 대한 선호도를 조사해요.
- 분량, 발간연도, 장르, 제외 요소와 같은 다양한 질문을 통해 책의 추천 범위를 좁히고, 사용자의 요구를 LLM을 통해 이해하고 구체화해요.

### 면담 질문 순서
1. **Q1_SQUIN**: 최근 읽었던 책이나 미디어에서 마음에 남은 이야기
2. **Q2_LENGTH**: 원하는 분량 (짧음/중간/장편)
3. **Q3_RECENCY**: 발간연도 선호도 (최근/무관)
4. **Q4_CONTEXT**: 중요하게 여기는 요소 (속도감, 성격 묘사, 설정 등)
5. **Q5_GENRE**: 선호하는 장르 (복수 선택 가능)
6. **Q7_NEG**: 피하고 싶은 요소
7. **Q8_END**: 핵심 키워드
   
### 2. 지능형 도서 추천
- **의미 기반 검색**: Sentence Transformers 또는 OpenAI 임베딩을 활용해서 의미 유사도를 계산해서, 사용자의 요구를 이해해요.
- **규칙 기반 점수**: 분량, 발간연도, 제외 키워드 답변 결과를 통해 추천 결과를 좁혀요.
- **인기도 점수**: 알라딘 API의 리뷰 점수와 판매량을 반영해서 도서의 전반적 인기에 대한 정보를 모아요.
- **하이브리드 랭킹**: 의미 유사도(55%) + 규칙 점수(25%) + 인기도(20%)를 모아서 최종 순위를 정하는 하이브리드 방식으로 도서를 추천해요.

### 3. 알라딘 API 연동
알라딘 TTB API를 통해 ISBN 기반 조회, 카테고리별 검색, 베스트셀러 조회를 수행하고 있어요.


## 📁 프로젝트 구조

```
new_book/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 메인 애플리케이션
│   ├── streamlit_app.py        # Streamlit 웹 인터페이스
│   ├── config.py               # 설정 관리
│   ├── models.py               # 데이터베이스 모델
│   ├── core/
│   │   ├── interview.py        # 면담 질문 및 답변 파싱
│   │   ├── nlp.py              # 임베딩 생성 (SBERT/OpenAI)
│   │   ├── ranker.py           # 도서 랭킹 알고리즘
│   │   └── state_machine.py    # 상태 관리
│   └── services/
│       ├── aladin.py           # 알라딘 API 클라이언트
│       ├── cache.py            # 캐싱 서비스
│       └── categories.py       # 카테고리 관리
├── requirements.txt            # Python 의존성
├── Dockerfile                  # Docker 이미지 정의
├── docker-compose.yml          # Docker Compose 설정
└── README.md                   # 프로젝트 문서
```

## 🚀 설치 및 실행

### 사전 요구사항

- Python 3.9 이상
- pip 또는 conda

### 1. 저장소 클론

```bash
git clone <repository-url>
cd new_book
```

### 2. 가상 환경 생성 및 활성화

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. API 서버 실행

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Streamlit 앱 실행

새 터미널에서:

```bash
streamlit run app/streamlit_app.py
```

브라우저에서 `http://localhost:8501`로 접속합니다.

## ⚙️ 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 변수들을 설정하세요:

```env
# 알라딘 TTB API 키 (필수)
ALADIN_TTB_KEY=your_aladin_api_key

# 임베딩 제공자 선택: "sbert" 또는 "openai" (기본값: sbert)
EMBEDDING_PROVIDER=sbert

# OpenAI API 키 (EMBEDDING_PROVIDER=openai일 때 필요)
OPENAI_API_KEY=your_openai_api_key

# 서버 설정 (선택 사항)
APP_HOST=0.0.0.0
APP_PORT=8000

# Streamlit에서 사용할 API 베이스 URL (선택 사항)
API_BASE=http://localhost:8000
```

### 알라딘 API 키 발급

[알라딘 개발자 센터](https://www.aladin.co.kr/ttb/api/api.aspx)에 접속해서 TTB API를 신청하고, 키를 발급받아주세요.

## 📚 API 문서

API 서버 실행 후 `http://localhost:8000/docs`에서 Swagger UI를 통해 API 문서를 확인할 수 있어요.

