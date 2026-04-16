# ICHS Backend (Django + DRF)

This scaffold matches the methodology chapter stack:
- Django + Django REST Framework + JWT
- PostgreSQL (PostGIS-ready design)
- Diagnosis, Geo-alerts, Weather risk, and Community modules

## Layout

- `backend/ichs/` core Django project settings and routing
- `backend/apps/users/` farmer auth and profile
- `backend/apps/diagnosis/` image/text/combined diagnosis endpoints
- `backend/apps/alerts/` outbreak alert generation + retrieval
- `backend/apps/weather/` weather ingestion + disease risk scoring
- `backend/apps/community/` farmer community posts

## Quick Start

```bash
pip install -r requirements.txt
cd backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

API root health endpoint:
- `GET /api/v1/health/`

Core endpoints:
- `POST /api/v1/auth/register/`
- `POST /api/v1/auth/token/`
- `POST /api/v1/predict/image/`
- `POST /api/v1/predict/text/`
- `POST /api/v1/predict/combined/`
- `GET /api/v1/alerts/`
- `POST /api/v1/weather/risk/`
- `GET/POST /api/v1/community/posts/`

## Notes

- Prediction services are stubs so frontend can integrate now.
- Replace `apps/diagnosis/services.py` with trained EfficientNet-B4 and BERT model serving.
- Alert service currently uses haversine fallback; move to SQL `ST_DWithin` queries once PostGIS migrations are enabled.


source .venv/bin/activate