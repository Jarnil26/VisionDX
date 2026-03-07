#!/bin/bash
# VisionDX Project Startup Script
# Starts both backend and frontend services

echo "======================================"
echo "  VisionDX - Full Stack Startup"
echo "======================================"
echo ""

# Check Python
echo "✓ Python version:"
python --version

# Check Node
echo ""
echo "✓ Node version:"
node --version

echo ""
echo "Starting services..."
echo ""

# Backend
echo "[1/2] Starting FastAPI Backend on http://localhost:8000"
echo "         API Docs: http://localhost:8000/docs"
cd d:\risu\VisionDX
start "VisionDX Backend" cmd /k "uvicorn visiondx.main:app --host 127.0.0.1 --port 8000 --reload"

# Wait for backend to start
timeout /t 3 /nobreak

# Frontend
echo "[2/2] Starting Next.js Frontend on http://localhost:3000"
cd d:\risu\VisionDX\frontend
start "VisionDX Frontend" cmd /k "npm run dev"

echo ""
echo "======================================"
echo "  Both services starting..."
echo "======================================"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "✓ Backend API Docs: http://localhost:8000/docs"
echo "✓ Backend API ReDoc: http://localhost:8000/redoc"
echo ""
