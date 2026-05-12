# ICHS - Inclusive Crop Health System

ICHS is a crop-health diagnosis platform with:

- Web app for image + symptom diagnosis
- Mobile app for camera + GPS capture
- Backend API for diagnosis, weather risk, and nearby outbreak context
- Optional CNN training on PlantVillage

## Stack

- Backend: Django, Django REST Framework, SimpleJWT
- ML: optional TensorFlow stack for training only, heuristic fallback before a trained model is available
- Web: React
- Mobile: Expo / React Native

## Repository Layout

```text
ICHS/
├── backend/
├── frontend/
│   ├── web/
│   └── mobile/
├── datasets/
├── models/
└── README.md
```

## What Works Now

- Web diagnosis with image upload, symptom text, location, weather risk, and nearby reports
- Mobile diagnosis with camera capture, symptoms, location, weather risk, and nearby reports
- Backend endpoints without forcing auth for the first run
- PlantVillage training script with local fallback behavior

## Setup

### 1. Python Backend

From the repo root:

```bash
cd /home/contractor/Koding/ICHS/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r ../requirements.txt
```

Create a local environment file if you want weather API access:

```bash
cp ../.env.example ../.env
```

Optional environment variables:

- `OPENWEATHER_API_KEY`
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DB_ENGINE` to switch away from SQLite

Run the backend:

```bash
python manage.py migrate --run-syncdb
python manage.py runserver 0.0.0.0:8000
```

Health check:

- `GET http://localhost:8000/api/v1/health/`

## Web App

The web app expects the backend at:

- `http://localhost:8000/api/v1`

If you need a different API host, set:

```bash
export REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
```

Then run:

```bash
cd /home/contractor/Koding/ICHS/frontend/web
npm install
npm run dev
```

### Background Video

Place the looping background video here:

- `frontend/web/public/media/background.mp4`

The web frontend uses `/media/background.mp4` automatically.

## Mobile App

The mobile app is a fresh Expo Go client for capture, symptoms, location, weather, and nearby alerts.
It now targets Expo SDK 55, so make sure Expo Go on your phone is updated to the latest version.

Run:

```bash
cd /home/contractor/Koding/ICHS/frontend/mobile
rm -rf node_modules package-lock.json .expo
npm install
npm run dev
```

Default API host behavior:

- Android emulator: `http://10.0.2.2:8000/api/v1`
- iOS simulator / desktop Expo web: `http://localhost:8000/api/v1`
- Real phone on LAN: set `EXPO_PUBLIC_API_BASE_URL` to your laptop's LAN IP, for example `http://192.168.1.20:8000/api/v1`

Override it if needed:

```bash
export EXPO_PUBLIC_API_BASE_URL=http://192.168.1.20:8000/api/v1
```

For a real phone, `localhost` will not work for the backend URL. Use your computer's LAN IP.

If Expo tries to open Android but your machine does not have the Android SDK, use one of these options:

- Physical phone: install Expo Go on the phone, then run `npm run dev` in `frontend/mobile` and scan the QR code.
- Android emulator: install Android Studio, then set `ANDROID_HOME` and add `platform-tools` to your `PATH`.

If Expo Go still shows `failed to download remote update`, try a different network or a phone hotspot. Some Wi-Fi networks block device-to-device traffic even when both devices are on the same SSID.

If Expo CLI keeps trying to reach `api.expo.dev`, keep using `npm run dev` in offline mode. That avoids Expo's version lookup and uses the local Metro bundler only.
The mobile app uses `expo-image-picker` and `expo-location`, so make sure permissions are granted on the device.

Example Android SDK shell setup:

```bash
export ANDROID_HOME="$HOME/Android/Sdk"
export PATH="$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$ANDROID_HOME/cmdline-tools/latest/bin"
```

If your SDK lives somewhere else, replace the path above with the actual install location.

## Training the CNN

The training script can use the extracted PlantVillage dataset. If the trained model is not present, the backend still works using heuristic prediction.

Install the optional ML stack only if you want to train the CNN:

```bash
pip install -r ../requirements-ml.txt
```

Prepare the dataset:

```bash
cd /home/contractor/Koding/ICHS
chmod +x download_datasets.sh
./download_datasets.sh
```

If you already extracted PlantVillage, make sure the images exist under:

- `datasets/images/plantvillage/raw/`

Train a lightweight smoke-test model:

```bash
cd /home/contractor/Koding/ICHS/backend
source .venv/bin/activate
python ml/train_cnn.py --subset default --epochs 1 --batch-size 4 --image-size 224 --weights none
```

Train a fuller model:

```bash
python ml/train_cnn.py --subset default --epochs 20 --batch-size 24 --image-size 380
```

Saved model outputs:

- `models/plantvillage_efficientnetb4_final.keras`
- `models/label_map.json`
- `models/history.json`
- `models/metrics_report.json`

## API Endpoints

### Diagnosis

- `POST /api/v1/diagnosis/combined/`
- `POST /api/v1/predict/combined/`
- `POST /api/v1/predict/image/`
- `POST /api/v1/predict/text/`
- `GET /api/v1/diagnosis/reports/`

### Weather

- `POST /api/v1/weather/risk/`

### Alerts

- `GET /api/v1/alerts/`

With coordinates:

```text
GET /api/v1/alerts/?latitude=6.5244&longitude=3.3792&radius=10
```

### Auth

- `POST /api/v1/auth/register/`
- `POST /api/v1/auth/token/`
- `POST /api/v1/auth/token/refresh/`

## Notes

- The backend defaults to SQLite for easier local setup.
- If you want PostgreSQL later, set `DB_ENGINE=django.db.backends.postgresql` and the DB connection variables.
- `OPENWEATHER_API_KEY` is optional. Without it, the weather endpoint uses deterministic local fallback data.

## Troubleshooting

- If the web background video does not appear, confirm `frontend/web/public/media/background.mp4` exists.
- If mobile cannot reach the backend, set `EXPO_PUBLIC_API_BASE_URL` to your machine’s LAN IP.
- If the backend cannot create tables, re-run:

```bash
python manage.py migrate --run-syncdb
```

## License

MIT
