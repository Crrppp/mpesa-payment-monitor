#!/bin/bash
echo "🚀 M-Pesa Payment Monitor Setup"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python backend/generate_key.py
cp .env.example .env
echo "✅ Setup complete! Edit .env with your credentials."