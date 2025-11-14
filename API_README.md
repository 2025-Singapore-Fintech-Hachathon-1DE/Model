# Singapore Detection System API

부정거래 탐지 시스템 REST API 서버

## 기능

-   **Bonus Laundering Detection** (증정금 녹이기): 보너스를 악용한 자금 세탁 패턴 탐지
-   **Funding Fee Hunter** (펀딩비 악용): 펀딩비 정산을 노린 고빈도 거래 탐지
-   **Cooperative Trading** (공모거래): 복수 계정 간 협력 거래 패턴 탐지

## 설치 및 실행

### 1. 의존성 설치

```bash
# 가상환경 생성 (최초 1회)
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. 서버 실행

#### 방법 1: 스크립트 사용 (권장)

```bash
./start_server.sh
```

#### 방법 2: 직접 실행

```bash
# 가상환경 활성화 후
python main.py
```

#### 방법 3: uvicorn 직접 실행

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 서버 확인

서버가 시작되면 다음 URL에서 확인할 수 있습니다:

-   **API 엔드포인트**: http://localhost:8000
-   **API 문서 (Swagger)**: http://localhost:8000/docs
-   **헬스 체크**: http://localhost:8000/health

## API 엔드포인트

### 통계

-   `GET /api/stats` - 전체 탐지 통계
-   `GET /api/hourly-distribution` - 시간대별 탐지 분포

### 제재 및 탐지

-   `GET /api/sanctions` - 모든 제재 케이스
    -   Query Params: `model` (wash/funding/cooperative), `limit`
-   `GET /api/top-accounts` - 상위 위반 계정
    -   Query Params: `limit` (기본 10)

### 시각화

-   `GET /api/timeseries` - 시간별 탐지 추이
    -   Query Params: `interval` (1h/1d)
-   `GET /api/visualization` - 시각화 데이터 (네트워크 그래프 등)
    -   Query Params: `model` (bonus/funding/cooperative)

### 원본 데이터

-   `GET /api/raw/{model}` - 특정 모델의 원본 데이터
    -   Path Params: `model` (bonus/funding/cooperative)

### 유틸리티

-   `POST /api/reload` - 데이터 강제 리로드

## 데이터 구조

### Output 폴더

서버 시작 시 `run_all_detections.py`가 실행되어 다음 위치에 결과를 저장:

```
output/
├── bonus/                 # Bonus Laundering 결과
│   ├── detection_config.json
│   ├── sanction_cases.json
│   ├── trade_pairs_detailed.csv
│   └── visualization_data.json
├── funding_fee/           # Funding Fee Hunter 결과
│   ├── detection_config.json
│   ├── sanction_accounts.json
│   ├── funding_hunter_cases.csv
│   ├── account_summaries.csv
│   └── visualization_data.json
└── cooperative/           # Cooperative Trading 결과
    ├── detection_config.json
    ├── sanction_groups.json
    ├── trade_pairs_detailed.csv
    ├── cooperative_groups.csv
    └── visualization_data.json
```

## 프론트엔드 연결

프론트엔드(Singapore_front)와 연결하려면:

1. 백엔드 서버 실행 (8000 포트)
2. 프론트엔드 개발 서버 실행 (5173 포트)

CORS는 다음 origin을 허용하도록 설정되어 있습니다:

-   http://localhost:5173
-   http://localhost:3000

## 개발

### 코드 구조

```
Singapore_back/
├── main.py                     # FastAPI 메인 서버
├── run_all_detections.py       # 탐지 모델 통합 실행
├── api/
│   ├── data_aggregator.py      # 데이터 통합 레이어
│   └── routers/
│       └── detection.py        # API 라우터
├── wash_trading/               # Bonus Laundering 모델
├── funding_fee/                # Funding Fee Hunter 모델
├── abusing/                    # Cooperative Trading 모델
└── common/                     # 공통 유틸리티
```

### 데이터 흐름

1. 서버 시작 시 `run_all_detections.py` 실행
2. 각 모델이 `output/` 폴더에 결과 저장
3. `DataAggregator`가 모든 결과 파일 읽기
4. API 엔드포인트를 통해 통합 데이터 제공

### 캐싱

`DataAggregator`는 5분 캐싱을 사용합니다. 강제로 리로드하려면:

```bash
curl -X POST http://localhost:8000/api/reload
```

## 문제 해결

### 포트가 이미 사용 중

```bash
# 8000 포트를 사용 중인 프로세스 찾기
lsof -i :8000

# 프로세스 종료
kill -9 <PID>
```

### 모듈을 찾을 수 없음

```bash
# 가상환경이 활성화되어 있는지 확인
which python

# 의존성 재설치
pip install -r requirements.txt --force-reinstall
```

### 탐지 모델 실행 실패

`output/` 폴더를 확인하여 각 모델의 결과 파일이 생성되었는지 확인:

```bash
ls -la output/bonus/
ls -la output/funding_fee/
ls -la output/cooperative/
```

## 라이센스

Singapore Fintech Hackathon 2025
