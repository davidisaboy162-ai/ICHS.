import React, { useEffect, useMemo, useRef, useState } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';
const DIAGNOSIS_URL = `${API_BASE_URL}/diagnosis/combined/`;
const WEATHER_URL = `${API_BASE_URL}/weather/risk/`;
const ALERTS_URL = `${API_BASE_URL}/alerts/`;

function getRecommendation(confidence) {
  if (confidence >= 0.8) return 'High confidence result. Start treatment immediately and notify nearby farmers.';
  if (confidence >= 0.6) return 'Moderate confidence result. Monitor closely and cross-check symptoms tomorrow.';
  return 'Low confidence result. Capture a clearer image or contact an extension officer.';
}

function App() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState('');
  const [symptoms, setSymptoms] = useState('');
  const [fieldName, setFieldName] = useState('Field A');
  const [manualLatitude, setManualLatitude] = useState('');
  const [manualLongitude, setManualLongitude] = useState('');
  const [prediction, setPrediction] = useState(null);
  const [weatherRisk, setWeatherRisk] = useState(null);
  const [nearbyAlerts, setNearbyAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [location, setLocation] = useState(null);
  const [locationState, setLocationState] = useState('Location not requested yet.');
  const [locationSupported, setLocationSupported] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!navigator.geolocation) {
      setLocationSupported(false);
      setLocationState('Geolocation is not supported in this browser.');
      return;
    }

    setLocationSupported(true);
  }, []);

  useEffect(() => {
    return () => {
      if (imagePreview) {
        URL.revokeObjectURL(imagePreview);
      }
    };
  }, [imagePreview]);

  const locationLabel = useMemo(() => {
    if (location) {
      return `${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}`;
    }
    return locationState;
  }, [location, locationState]);

  const resolvedLatitude = useMemo(() => {
    if (location?.latitude !== undefined && location?.latitude !== null) {
      return location.latitude;
    }
    const parsed = Number(manualLatitude);
    return Number.isFinite(parsed) ? parsed : 0;
  }, [location, manualLatitude]);

  const resolvedLongitude = useMemo(() => {
    if (location?.longitude !== undefined && location?.longitude !== null) {
      return location.longitude;
    }
    const parsed = Number(manualLongitude);
    return Number.isFinite(parsed) ? parsed : 0;
  }, [location, manualLongitude]);

  const requestBrowserLocation = () => {
    if (!navigator.geolocation) {
      setLocationSupported(false);
      setLocationState('Geolocation is not supported in this browser.');
      return;
    }

    setLocationState('Requesting browser location...');
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
        setLocationState('Location ready');
      },
      (err) => {
        if (err?.code === 1) {
          setLocationState('Location permission denied. Enter coordinates manually.');
        } else if (err?.code === 2) {
          setLocationState('Location unavailable. Check browser permissions or GPS.');
        } else {
          setLocationState('Could not read browser location.');
        }
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 }
    );
  };

  const handleImageSelect = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setSelectedImage(file);
    setImagePreview(URL.createObjectURL(file));
  };

  const normalizeImageFile = async (file) => {
    const imageUrl = URL.createObjectURL(file);
    const image = new Image();

    await new Promise((resolve, reject) => {
      image.onload = resolve;
      image.onerror = reject;
      image.src = imageUrl;
    });

    const maxDimension = 1280;
    const scale = Math.min(1, maxDimension / Math.max(image.width, image.height));
    const canvas = document.createElement('canvas');
    canvas.width = Math.round(image.width * scale);
    canvas.height = Math.round(image.height * scale);
    const context = canvas.getContext('2d');
    context.drawImage(image, 0, 0, canvas.width, canvas.height);

    URL.revokeObjectURL(imageUrl);

    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.92));
    if (!blob) {
      return file;
    }

    return new File([blob], file.name.replace(/\.\w+$/, '.jpg'), {
      type: 'image/jpeg',
      lastModified: Date.now(),
    });
  };

  const fetchNearbyAlerts = async (lat, lon) => {
    const url = new URL(ALERTS_URL);
    url.searchParams.set('latitude', String(lat));
    url.searchParams.set('longitude', String(lon));
    url.searchParams.set('radius', '10');

    const response = await fetch(url.toString());
    const result = await response.json();
    setNearbyAlerts(Array.isArray(result.results) ? result.results : []);
  };

  const handleSubmit = async () => {
    if (!selectedImage && !symptoms.trim()) {
      setErrorMessage('Upload an image, enter symptoms, or do both before running diagnosis.');
      return;
    }

    setErrorMessage('');
    setLoading(true);
    setPrediction(null);
    setWeatherRisk(null);

    try {
      const formData = new FormData();
      if (selectedImage) {
        const normalized = await normalizeImageFile(selectedImage);
        formData.append('file', normalized);
      }
      if (symptoms.trim()) {
        formData.append('symptoms', symptoms.trim());
      }
      formData.append('latitude', String(resolvedLatitude ?? 0));
      formData.append('longitude', String(resolvedLongitude ?? 0));
      formData.append('location_name', fieldName.trim() || 'Current field');

      const diagnosisResponse = await fetch(DIAGNOSIS_URL, {
        method: 'POST',
        body: formData,
      });

      const diagnosisResult = await diagnosisResponse.json();
      if (!diagnosisResponse.ok) {
        throw new Error(diagnosisResult.detail || diagnosisResult.error || 'Diagnosis request failed.');
      }

      setPrediction(diagnosisResult);

      if (Number.isFinite(resolvedLatitude) && Number.isFinite(resolvedLongitude)) {
        const weatherResponse = await fetch(WEATHER_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            latitude: resolvedLatitude,
            longitude: resolvedLongitude,
            location_name: fieldName.trim() || 'Current field',
          }),
        });
        const weatherResult = await weatherResponse.json();
        if (weatherResponse.ok) {
          setWeatherRisk(weatherResult);
        }

        await fetchNearbyAlerts(resolvedLatitude, resolvedLongitude);
      }
    } catch (error) {
      setErrorMessage(error.message || 'Failed to get diagnosis. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const combinedConfidence = prediction?.confidence || 0;

  return (
    <div className="app-shell">
      <video className="app-bg-video" autoPlay loop muted playsInline aria-hidden="true">
        <source src="/media/background.mp4" type="video/mp4" />
      </video>
      <div className="app-overlay" />

      <header className="hero">
        <div className="hero__content">
          <p className="hero__eyebrow">Inclusive Crop Health System</p>
          <h1>Field-ready disease diagnosis for real farmers.</h1>
          <p className="hero__subtitle">
            Upload a crop image, describe symptoms, and get diagnosis, weather risk, and nearby outbreak awareness in one flow.
          </p>
        </div>
          <div className="hero__status">
          <div className="status-chip">Location: {locationLabel}</div>
          <div className="status-chip">{locationSupported ? 'Manual fallback enabled' : 'Geolocation unavailable'}</div>
          <div className="status-chip">Video background: enabled</div>
        </div>
      </header>

      <main className="dashboard">
        <section className="card card--editor">
          <div className="card__head">
            <div>
              <h2>New Diagnosis</h2>
              <p>Capture image, symptoms, and location in one request.</p>
            </div>
            <span className="pill pill--warm">AI assisted</span>
          </div>

          <div className="editor-grid">
            <div className="panel">
              <label className="label">Leaf Image</label>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleImageSelect}
                accept="image/*"
                className="hidden-input"
              />
              <button className="button button--ghost" onClick={() => fileInputRef.current?.click()}>
                {selectedImage ? 'Replace image' : 'Upload image'}
              </button>

              <div className="preview-frame">
                {imagePreview ? (
                  <img src={imagePreview} alt="Crop preview" className="preview-image" />
                ) : (
                  <div className="preview-empty">
                    <span>No image selected yet.</span>
                  </div>
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
                rows={10}
                className="textarea"
              />
              <p className="helper">Include crop type, symptom color, and where it started.</p>
            </div>
          </div>

          <div className="location-grid">
            <div className="panel">
              <label className="label" htmlFor="fieldName">Field name</label>
              <input
                id="fieldName"
                value={fieldName}
                onChange={(e) => setFieldName(e.target.value)}
                placeholder="North plot"
                className="input"
              />
            </div>
            <div className="panel">
              <label className="label">Browser location</label>
              <div className="location-actions">
                <button className="button button--ghost" onClick={requestBrowserLocation}>
                  Use browser location
                </button>
                <span className="helper">{locationState}</span>
              </div>
            </div>
            <div className="panel">
              <label className="label" htmlFor="manualLatitude">Latitude</label>
              <input
                id="manualLatitude"
                value={manualLatitude}
                onChange={(e) => setManualLatitude(e.target.value)}
                placeholder="e.g. 6.5244"
                className="input"
              />
            </div>
            <div className="panel">
              <label className="label" htmlFor="manualLongitude">Longitude</label>
              <input
                id="manualLongitude"
                value={manualLongitude}
                onChange={(e) => setManualLongitude(e.target.value)}
                placeholder="e.g. 3.3792"
                className="input"
              />
            </div>
          </div>

          {errorMessage && <div className="feedback feedback--error">{errorMessage}</div>}

          <div className="actions">
            <button className="button button--primary" onClick={handleSubmit} disabled={loading}>
              {loading ? 'Analyzing crop health...' : 'Run Diagnosis'}
            </button>
          </div>
        </section>

        <aside className="card card--insights">
          <div className="card__head">
            <div>
              <h2>Field Status</h2>
              <p>Location, alerts, and weather context.</p>
            </div>
          </div>

          <div className="metric">
            <span className="metric__label">Location</span>
            <strong>{locationLabel}</strong>
          </div>

          <div className="metric">
            <span className="metric__label">Nearby alerts</span>
            <strong>{nearbyAlerts.length}</strong>
          </div>

          <div className="metric">
            <span className="metric__label">Weather risk</span>
            <strong>{weatherRisk?.risk_level || 'Pending'}</strong>
          </div>

          <div className="insight-list">
            <p>Supports image and text diagnosis.</p>
            <p>Works with geolocation when permission is granted.</p>
            <p>Returns weather risk and nearby outbreak context after submit.</p>
          </div>
        </aside>

        <section className="card card--result">
          <div className="card__head">
            <div>
              <h2>Diagnosis Result</h2>
              <p>Backend response from the current submission.</p>
            </div>
            <span className="pill pill--green">Confidence {(combinedConfidence * 100).toFixed(1)}%</span>
          </div>

          {prediction ? (
            <div className="result-stack">
              <div className="result-line">
                <span>Status</span>
                <strong>{prediction.status || 'success'}</strong>
              </div>
              <div className="result-line">
                <span>Disease</span>
                <strong>{prediction.disease_name || prediction.predicted_disease?.name || 'Unknown'}</strong>
              </div>
              <div className="result-line">
                <span>Recommendation</span>
                <strong>{getRecommendation(combinedConfidence)}</strong>
              </div>
              <div className="result-line">
                <span>Alerts triggered</span>
                <strong>{prediction.alerts_count ?? 0}</strong>
              </div>
              {weatherRisk && (
                <div className="weather-box">
                  <strong>Weather risk: {weatherRisk.risk_level}</strong>
                  <p>{weatherRisk.explanation}</p>
                </div>
              )}
              {nearbyAlerts.length > 0 && (
                <div className="alerts-box">
                  <strong>Nearby reports</strong>
                  <ul>
                    {nearbyAlerts.slice(0, 4).map((item) => (
                      <li key={`${item.report_id}-${item.created_at}`}>
                        {item.disease} - {item.distance_km} km away
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="result-empty">
              Submit a diagnosis to see the model output, confidence, and weather context here.
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
