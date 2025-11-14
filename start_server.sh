#!/bin/bash

# Singapore Detection System - Backend Server Startup Script

echo "=========================================="
echo "Singapore Detection System"
echo "Backend API Server"
echo "=========================================="
echo ""

# 가상환경 활성화
if [ -d "venv" ]; then
    echo "✓ Activating virtual environment..."
    source venv/bin/activate
else
    echo "✗ Virtual environment not found!"
    echo "  Please run: python3 -m venv venv"
    echo "  Then run: source venv/bin/activate"
    echo "  Then run: pip install -r requirements.txt"
    exit 1
fi

# 의존성 확인
echo "✓ Checking dependencies..."
python -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "✗ FastAPI or Uvicorn not installed!"
    echo "  Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "=========================================="
echo "Starting API Server..."
echo "=========================================="
echo ""
echo "  API URL: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# 서버 실행
python main.py
