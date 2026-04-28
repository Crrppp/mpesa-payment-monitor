# 💳 M-Pesa Payment Monitor

Real-time M-Pesa transaction tracking for businesses with Paybill/Till numbers.

## Quick Start
1. Clone repo
2. Run `setup.sh` (Mac/Linux) or manually create venv and install requirements
3. Copy `.env.example` to `.env` and add your credentials
4. Run `database/schema.sql` in MySQL
5. Start backend: `./run_backend.sh`
6. Start dashboard: `./run_dashboard.sh`

## Deploy to Render
- Push to GitHub
- Create two Web Services using `render.yaml` blueprint
- Add environment variables
- Register Daraja webhook: `python backend/register_daraja.py https://mpesa-backend.onrender.com`