"""
FastAPI Main Server for Detection System
부정거래 탐지 시스템 API 서버
"""

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from api.routers import detection, simulation


@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작/종료 시 실행"""
    print("\n" + "="*80)
    print(" " * 20 + "Singapore Detection System API Starting...")
    print("="*80 + "\n")
    
    # 서버 시작 시 탐지 실행
    print("Running detection models...")
    try:
        from run_all_detections import run_all_detections
        results = run_all_detections("problem_data_final.xlsx")
        print("\n✓ Detection models completed successfully!")
        print(f"  - Bonus: {results.get('bonus', {}).get('passed_filter', 0)} cases")
        print(f"  - Funding: {results.get('funding', {}).get('passed_filter', 0)} cases")
        print(f"  - Cooperative: {results.get('cooperative', {}).get('passed_filter', 0)} cases")
    except Exception as e:
        print(f"\n✗ Error running detection models: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print(" " * 20 + "API Server Ready!")
    print(" " * 20 + "Access at: http://localhost:8000")
    print(" " * 20 + "Docs at: http://localhost:8000/docs")
    print("="*80 + "\n")
    
    yield
    
    # 서버 종료 시
    print("\n" + "="*80)
    print(" " * 20 + "API Server Shutting Down...")
    print("="*80 + "\n")


# FastAPI 앱 생성
app = FastAPI(
    title="Singapore Detection System API",
    description="부정거래 탐지 시스템 REST API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 설정 (프론트엔드 연결)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite 개발 서버
        "http://localhost:3000",  # 백업 포트
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(detection.router, prefix="/api", tags=["detection"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["simulation"])


@app.get("/")
async def root():
    """API 루트"""
    return {
        "message": "Singapore Detection System API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "stats": "/api/stats",
            "sanctions": "/api/sanctions",
            "timeseries": "/api/timeseries",
            "top_accounts": "/api/top-accounts",
            "hourly_distribution": "/api/hourly-distribution",
            "visualization": "/api/visualization",
            "simulation_status": "/api/simulation/status",
            "simulation_advance": "/api/simulation/advance",
            "simulation_reset": "/api/simulation/reset",
        }
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 개발 모드에서 자동 리로드
        log_level="info",
    )
