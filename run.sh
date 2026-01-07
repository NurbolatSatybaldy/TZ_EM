#!/bin/bash

# Quick start script for the authentication system

echo "🚀 Starting Authentication & Authorization System"
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please create it based on .env.example"
    echo "You can copy .env.example to .env and update the values:"
    echo "  cp .env.example .env"
    exit 1
fi

# Check if database is seeded
echo "🌱 Checking database..."
python -c "from database import SessionLocal; from models import Role; db = SessionLocal(); exists = db.query(Role).first() is not None; db.close(); exit(0 if exists else 1)"

if [ $? -ne 0 ]; then
    echo "🌱 Seeding database with initial data..."
    python seed_data.py
fi

# Start the application
echo ""
echo "✅ Starting FastAPI application..."
echo "📖 API Documentation will be available at:"
echo "   - Swagger UI: http://localhost:8000/docs"
echo "   - ReDoc: http://localhost:8000/redoc"
echo ""
uvicorn main:app --reload

