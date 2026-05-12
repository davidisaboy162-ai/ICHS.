# ICHS Backend

The backend is a Django REST API with:

- diagnosis endpoints for image, text, and combined input
- weather risk scoring
- nearby alert lookup
- optional JWT auth

## Quick Start

```bash
cd /home/contractor/Koding/ICHS/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r ../requirements.txt
python manage.py migrate --run-syncdb
python manage.py runserver 0.0.0.0:8000
```

## Notes

- SQLite is the default database for local development.
- To use PostgreSQL, set `DB_ENGINE=django.db.backends.postgresql` and the DB variables in `.env`.
- `OPENWEATHER_API_KEY` is optional. Without it, the weather endpoint uses deterministic fallback data.
- The diagnosis engine uses the trained CNN model if `models/plantvillage_efficientnetb4_final.keras` exists. Otherwise it falls back to deterministic heuristics so the API still works.
- Only install `../requirements-ml.txt` if you want to train the CNN. It is not needed to run the backend or frontend.
- For the mobile app, Expo can run on a physical phone without Android SDK. If you want an emulator, install Android Studio and set `ANDROID_HOME` plus `platform-tools` in your `PATH`.
- On a physical phone, set `EXPO_PUBLIC_API_BASE_URL` to your backend LAN IP. `localhost` will not reach your laptop from the phone.
- If Expo Go reports `failed to download remote update`, use `npm run dev` again after a clean start, or switch to a hotspot if your Wi-Fi blocks LAN traffic.
- If Expo CLI cannot reach `api.expo.dev`, use the offline mode that `npm run dev` now points to.
- The mobile package is Expo Go focused and uses `expo-image-picker` plus `expo-location` for capture and GPS.
- The mobile app now targets Expo SDK 55, so Expo Go on the phone must be the latest store version.

## Important Paths

- `backend/ichs/settings.py`
- `backend/apps/diagnosis/services.py`
- `backend/ml/train_cnn.py`

## Main Endpoints

- `POST /api/v1/diagnosis/combined/`
- `POST /api/v1/predict/combined/`
- `POST /api/v1/weather/risk/`
- `GET /api/v1/alerts/?latitude=...&longitude=...`
- `GET /api/v1/health/`
