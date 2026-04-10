"""
React Web App for ICHS
Web interface for crop disease diagnosis
"""

import React, { useState, useRef } from 'react';
import './App.css';

function App() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [symptoms, setSymptoms] = useState('');
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [location, setLocation] = useState(null);
  const fileInputRef = useRef(null);

  // Get user location
  React.useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          });
        },
        (error) => {
          console.log('Location access denied:', error);
        }
      );
    }
  }, []);

  const handleImageSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedImage(file);
      // Preview image
      const reader = new FileReader();
      reader.onload = (e) => {
        document.getElementById('imagePreview').src = e.target.result;
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async () => {
    if (!selectedImage && !symptoms.trim()) {
      alert('Please provide either an image or symptom description');
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();

      if (selectedImage) {
        formData.append('file', selectedImage);
      }

      if (symptoms.trim()) {
        formData.append('symptoms', symptoms);
      }

      if (location) {
        formData.append('latitude', location.latitude.toString());
        formData.append('longitude', location.longitude.toString());
      }

      const response = await fetch('http://localhost:8000/predict/combined', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      setPrediction(result);

    } catch (error) {
      alert('Failed to get diagnosis. Please try again.');
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>ICHS - Inclusive Crop Health System</h1>
        <p>Crop Disease Diagnosis for Farmers</p>
      </header>

      <main className="App-main">
        <div className="diagnosis-container">
          <h2>Crop Health Diagnosis</h2>

          {/* Image Upload Section */}
          <div className="upload-section">
            <h3>Upload Crop Image</h3>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageSelect}
              accept="image/*"
              style={{ display: 'none' }}
            />
            <button
              className="upload-btn"
              onClick={() => fileInputRef.current.click()}
            >
              Choose Image
            </button>
            <div className="image-preview">
              <img id="imagePreview" alt="Crop preview" style={{ maxWidth: '300px', maxHeight: '300px' }} />
            </div>
          </div>

          {/* Symptom Description */}
          <div className="symptom-section">
            <h3>Describe Symptoms (Optional)</h3>
            <textarea
              placeholder="Describe what you observe on your crops... (e.g., yellow spots, wilting leaves, etc.)"
              value={symptoms}
              onChange={(e) => setSymptoms(e.target.value)}
              rows={4}
              className="symptom-input"
            />
          </div>

          {/* Submit Button */}
          <button
            className={`submit-btn ${loading ? 'loading' : ''}`}
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? 'Analyzing...' : 'Get Diagnosis'}
          </button>

          {/* Results */}
          {prediction && (
            <div className="results-section">
              <h3>Diagnosis Results</h3>
              <div className="result-card">
                <p><strong>Status:</strong> {prediction.status}</p>
                {prediction.prediction && (
                  <>
                    <p><strong>Combined Confidence:</strong> {(prediction.prediction.combined_confidence * 100).toFixed(1)}%</p>
                    <p><strong>Recommendation:</strong>
                      {prediction.prediction.combined_confidence > 0.8 ? ' High confidence - take immediate action' :
                       prediction.prediction.combined_confidence > 0.6 ? ' Moderate confidence - monitor closely' :
                       ' Low confidence - consult local extension service'}
                    </p>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="App-footer">
        <p>&copy; 2024 ICHS - Inclusive Crop Health System</p>
      </footer>
    </div>
  );
}

export default App;
