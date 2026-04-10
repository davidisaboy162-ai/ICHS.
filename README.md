# ICHS - Inclusive Crop Health System

## Machine Learning Project for Crop Disease Diagnosis

An intelligent platform designed to maximize inclusivity with:
- **Image-based diagnosis** using Convolutional Neural Networks (CNNs) for farmers with smartphone access
- **Text-based diagnosis** using Natural Language Processing (NLP) for farmers with basic devices
- **Geo-tagging and alerts** for neighboring farmers about potential outbreak threats

## Project Structure

```
ICHS/
├── data/
│   ├── raw/              # Original datasets
│   └── processed/        # Cleaned and preprocessed data
├── models/               # Trained model files and checkpoints
├── notebooks/            # Jupyter notebooks for exploration
├── src/                  # Source code modules
├── tests/                # Unit tests
├── config/               # Configuration files
├── logs/                 # Log files
└── requirements.txt      # Project dependencies
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Place raw datasets in `data/raw/`

3. Configure settings in `config/config.yaml`

4. Run preprocessing and training scripts

## Key Components

- **CNN Model**: Crop disease detection from images
- **NLP Model**: Symptom analysis from text descriptions
- **Data Pipeline**: End-to-end preprocessing and augmentation
- **Model Evaluation**: Performance metrics and validation
