# ICHS - Inclusive Crop Health System

## 🌱 AI-Powered Crop Disease Diagnosis for Farmers

An intelligent platform designed to maximize inclusivity with dual diagnosis capabilities:
- **📸 Image-based diagnosis** using Convolutional Neural Networks (CNNs) for farmers with smartphone access
- **💬 Text-based diagnosis** using Natural Language Processing (NLP) for farmers with basic devices
- **📍 Geo-tagging and alerts** for neighboring farmers about potential outbreak threats

## 🏗️ Project Structure

```
ICHS/
├── frontend/              # User interfaces
│   ├── mobile/           # React Native app (camera + GPS)
│   ├── web/             # React web app with Leaflet maps
│   └── shared/          # Shared components
├── backend/              # Django REST backend
│   ├── ichs/            # Django project config
│   ├── apps/            # Modular domain apps
│   │   ├── users/       # JWT auth + farmer profiles
│   │   ├── diagnosis/   # Image/text/combined diagnosis APIs
│   │   ├── alerts/      # Hyper-local outbreak alerts
│   │   ├── weather/     # Weather-linked risk scoring
│   │   └── community/   # Farmer community hub
│   ├── ml/              # ML models & training scripts
│   └── README.md        # Backend setup details
├── datasets/            # Data management
│   ├── images/          # Image datasets
│   │   └── raw/        # Raw crop images
│   ├── text/           # Text datasets
│   ├── processed/      # Processed data
│   └── dataset_manager.py # Dataset utilities
├── models/              # Trained model files
├── config/              # Configuration files
├── logs/                # Application logs
├── notebooks/           # Jupyter notebooks
├── tests/               # Unit tests
├── Docs/                # Documentation
└── requirements.txt     # Dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### 1. Clone and Setup
```bash
git clone <repository-url>
cd ICHS
```

### 2. Setup Backend
```bash
# Install Python dependencies
pip install -r requirements.txt

# Download datasets (see DATASET_SETUP.md)
./download_datasets.sh

# Start Django API server
cd backend
python manage.py migrate
python manage.py runserver
```
Backend will run on: `http://localhost:8000`

### 3. Setup Frontend
```bash
# Install frontend dependencies
./setup_frontend.sh

# Start the web app
cd frontend/web
npm start
```
Frontend will run on: `http://localhost:3000`

## 🎨 Frontend Features

### 🌐 Web Application
- **Interactive Map**: Leaflet-powered map showing disease outbreaks
- **Disease Alerts**: Real-time notifications about nearby outbreaks
- **Dual Diagnosis**: Image upload + symptom description
- **Agricultural Theme**: Nature-inspired design with green color palette
- **Responsive Design**: Works on desktop and mobile devices

### 📱 Mobile App (React Native)
- **Camera Integration**: Direct photo capture from device
- **GPS Location**: Automatic geo-tagging of reports
- **Offline Capability**: Basic functionality without internet
- **Push Notifications**: Alert system for disease outbreaks

## 🧠 Backend Features

### 🤖 Machine Learning Pipeline
- **CNN Models**: ResNet50/EfficientNet for image classification
- **NLP Models**: BERT/DistilBERT for symptom analysis
- **Combined Prediction**: Multi-modal diagnosis with confidence scoring

### 🗺️ Geo-Spatial Services
- **Location Tracking**: GPS coordinates for all reports
- **Alert System**: Notify farmers within configurable radius
- **Outbreak Mapping**: Visualize disease spread patterns

### 🔌 API Endpoints
```
POST /api/v1/predict/image/      # Image-based diagnosis
POST /api/v1/predict/text/       # Text-based diagnosis
POST /api/v1/predict/combined/   # Multi-modal diagnosis
GET  /api/v1/alerts/             # Get alerts for authenticated farmer
POST /api/v1/weather/risk/       # Weather-linked disease risk
GET/POST /api/v1/community/posts/ # Community hub posts
```

## 📊 Datasets

### Image Datasets
- **PlantVillage Dataset**: 54,000+ labeled crop disease images
- **14 plant species, 38 disease classes**
- **Supported formats**: JPG, PNG

### Text Datasets
- **Symptom descriptions** from agricultural extension services
- **Multi-language support** for global farmers
- **CSV format** with disease labels and confidence scores

## 🛠️ Development

### Running Tests
```bash
# Backend tests
python -m pytest tests/

# Frontend tests
cd frontend/web && npm test
```

### Training Models
```bash
cd backend/ml
python models.py  # Train CNN and NLP models
```

### Configuration
Edit `config/config.yaml` to customize:
- Model parameters
- Dataset paths
- API settings
- Alert radius

## 🌍 Impact & Inclusivity

### For Smartphone Users
- **Visual Diagnosis**: Take photos of affected crops
- **Instant Results**: AI-powered analysis in seconds
- **Location Services**: Contribute to community health monitoring

### For Basic Device Users
- **Text Description**: Describe symptoms in natural language
- **Voice Input**: Future support for voice descriptions
- **SMS Alerts**: Receive notifications via text messaging

### Community Benefits
- **Early Warning**: Prevent disease spread through alerts
- **Data Collection**: Build comprehensive crop health database
- **Farmer Empowerment**: Access to expert-level diagnosis anywhere

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **PlantVillage Dataset** for comprehensive crop disease images
- **OpenStreetMap** for mapping services
- **Agricultural extension services** worldwide for symptom databases

---

**ICHS** - Empowering farmers with AI for healthier crops and sustainable agriculture 🌾
