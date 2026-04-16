import React, { useMemo, useRef, useState } from 'react';
import './App.css';

const API_URL = 'http://localhost:8000/predict/combined';

function getRecommendation(confidence) {
  if (confidence >= 0.8) return 'High confidence result. Start treatment immediately and notify nearby farmers.';
  if (confidence >= 0.6) return 'Moderate confidence result. Monitor closely and cross-check symptoms tomorrow.';
  return 'Low confidence result. Capture a clearer image or contact an extension officer.';
}

function App() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState('');
  const [symptoms, setSymptoms] = useState('');
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [location, setLocation] = useState(null);
  const [locationError, setLocationError] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const fileInputRef = useRef(null);

  React.useEffect(() => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported in this browser.');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
      },
      () => {
        setLocationError('Location permission denied. Diagnosis will still work without location alerts.');
      },
      { enableHighAccuracy: false, timeout: 8000 }
    );
  }, []);

  const locationLabel = useMemo(() => {
    if (location) {
      return `${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}`;
    }
    return locationError || 'Locating your farm...';
  }, [location, locationError]);

  const handleImageSelect = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setSelectedImage(file);
    setImagePreview(URL.createObjectURL(file));
  };

  const handleSubmit = async () => {
    if (!selectedImage && !symptoms.trim()) {
      setErrorMessage('Please upload an image, add symptoms, or provide both before running diagnosis.');
      return;
    }

    setErrorMessage('');
    setLoading(true);
    setPrediction(null);

    try {
      const formData = new FormData();
      if (selectedImage) formData.append('file', selectedImage);
      if (symptoms.trim()) formData.append('symptoms', symptoms.trim());

      if (location) {
        formData.append('latitude', String(location.latitude));
        formData.append('longitude', String(location.longitude));
      } else {
        formData.append('latitude', '0');
        formData.append('longitude', '0');
      }

      const response = await fetch(API_URL, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.error || 'Diagnosis request failed.');
      }

      setPrediction(result);
    } catch (error) {
      setErrorMessage(error.message || 'Failed to get diagnosis. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const combinedConfidence = prediction?.prediction?.combined_confidence || 0;

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero__content">
          <p className="hero__eyebrow">Inclusive Crop Health System</p>
          <h1>Field-ready disease diagnosis for real farmers.</h1>
          <p className="hero__subtitle">
            Upload leaf images, add symptom notes, and get actionable diagnosis guidance in one clean workflow.
          </p>
        </div>
      </header>

      <main className="page">
        <section className="card card--primary">
          <div className="card__head">
            <h2>New Diagnosis</h2>
            <span className="status-pill">Location: {locationLabel}</span>
          </div>

          <div className="diagnosis-grid">
            <div className="panel">
              <label className="label">Leaf Image</label>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleImageSelect}
                accept="image/*"
                style={{ display: 'none' }}
              />
              <button className="button button--ghost" onClick={() => fileInputRef.current?.click()}>
                {selectedImage ? 'Change Image' : 'Upload Image'}
              </button>

              <div className="preview-frame">
                {imagePreview ? (
                  <img src={imagePreview} alt="Crop preview" className="preview-image" />
                ) : (
                  <p className="preview-placeholder">No image selected yet.</p>
                )}
              </div>
            </div>

            <div className="panel">
              <label className="label" htmlFor="symptoms">
                Symptoms Description
              </label>
              <textarea
                id="symptoms"
                placeholder="Example: brown patches on lower leaves, white powder on stem, yellowing edges..."
                value={symptoms}
                onChange={(e) => setSymptoms(e.target.value)}
                rows={9}
                className="textarea"
              />
              <p className="helper">Tip: include crop type, color changes, and where symptoms started.</p>
            </div>
          </div>

          {errorMessage && <div className="feedback feedback--error">{errorMessage}</div>}

          <div className="actions">
            <button className="button button--primary" onClick={handleSubmit} disabled={loading}>
              {loading ? 'Analyzing crop health...' : 'Run Diagnosis'}
            </button>
          </div>
        </section>

        <aside className="card card--side">
          <h3>How this helps</h3>
          <ul className="checklist">
            <li>Supports both image and text input.</li>
            <li>Built for low-bandwidth farm environments.</li>
            <li>Ready for geo-alert and weather risk integration.</li>
          </ul>
        </aside>

        {prediction && (
          <section className="card card--result">
            <div className="card__head">
              <h2>Diagnosis Result</h2>
              <span className="confidence-pill">Confidence: {(combinedConfidence * 100).toFixed(1)}%</span>
            </div>
            <p className="result-line">
              <strong>Status:</strong> {prediction.status || 'success'}
            </p>
            <p className="result-line">
              <strong>Recommendation:</strong> {getRecommendation(combinedConfidence)}
            </p>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
