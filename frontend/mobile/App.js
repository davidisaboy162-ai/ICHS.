"""
React Native Mobile App for ICHS
Camera interface and symptom input for farmers
"""

import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Image,
  TextInput,
  Alert,
  StyleSheet,
  SafeAreaView
} from 'react-native';
import {Camera} from 'expo-camera';
import * as Location from 'expo-location';

const ICHSMobileApp = () => {
  const [hasPermission, setHasPermission] = useState(null);
  const [camera, setCamera] = useState(null);
  const [image, setImage] = useState(null);
  const [symptoms, setSymptoms] = useState('');
  const [location, setLocation] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      const {status} = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === 'granted');

      const {status: locationStatus} = await Location.requestForegroundPermissionsAsync();
      if (locationStatus === 'granted') {
        const userLocation = await Location.getCurrentPositionAsync({});
        setLocation(userLocation.coords);
      }
    })();
  }, []);

  const takePicture = async () => {
    if (camera) {
      const photo = await camera.takePictureAsync();
      setImage(photo.uri);
    }
  };

  const submitDiagnosis = async () => {
    if (!image && !symptoms.trim()) {
      Alert.alert('Error', 'Please provide either an image or symptom description');
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();

      if (image) {
        const response = await fetch(image);
        const blob = await response.blob();
        formData.append('file', blob, 'crop_image.jpg');
      }

      if (symptoms.trim()) {
        formData.append('symptoms', symptoms);
      }

      // Add location data
      if (location) {
        formData.append('latitude', location.latitude.toString());
        formData.append('longitude', location.longitude.toString());
      }

      const response = await fetch('http://your-api-url:8000/predict/combined', {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const result = await response.json();
      setPrediction(result);

    } catch (error) {
      Alert.alert('Error', 'Failed to get diagnosis. Please try again.');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  if (hasPermission === null) {
    return <View><Text>Requesting camera permission...</Text></View>;
  }

  if (hasPermission === false) {
    return <View><Text>No access to camera</Text></View>;
  }

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>ICHS - Crop Health Diagnosis</Text>

      {/* Camera Section */}
      <View style={styles.cameraContainer}>
        <Camera
          ref={ref => setCamera(ref)}
          style={styles.camera}
          type={Camera.Constants.Type.back}
        >
          <TouchableOpacity style={styles.captureButton} onPress={takePicture}>
            <Text style={styles.captureText}>Take Photo</Text>
          </TouchableOpacity>
        </Camera>
      </View>

      {image && (
        <View style={styles.imagePreview}>
          <Image source={{uri: image}} style={styles.previewImage} />
        </View>
      )}

      {/* Symptom Input */}
      <View style={styles.inputContainer}>
        <Text style={styles.label}>Describe Symptoms (Optional):</Text>
        <TextInput
          style={styles.textInput}
          multiline
          placeholder="Describe what you see on your crops..."
          value={symptoms}
          onChangeText={setSymptoms}
        />
      </View>

      {/* Submit Button */}
      <TouchableOpacity
        style={[styles.submitButton, loading && styles.disabledButton]}
        onPress={submitDiagnosis}
        disabled={loading}
      >
        <Text style={styles.submitText}>
          {loading ? 'Analyzing...' : 'Get Diagnosis'}
        </Text>
      </TouchableOpacity>

      {/* Results */}
      {prediction && (
        <View style={styles.resultContainer}>
          <Text style={styles.resultTitle}>Diagnosis Result:</Text>
          <Text>Disease: {prediction.prediction?.combined_confidence > 0.7 ? 'High Confidence' : 'Needs Review'}</Text>
          <Text>Confidence: {(prediction.prediction?.combined_confidence * 100).toFixed(1)}%</Text>
        </View>
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginVertical: 20,
    color: '#2e7d32',
  },
  cameraContainer: {
    flex: 1,
    marginHorizontal: 20,
    marginBottom: 20,
  },
  camera: {
    flex: 1,
    borderRadius: 10,
    overflow: 'hidden',
  },
  captureButton: {
    position: 'absolute',
    bottom: 20,
    alignSelf: 'center',
    backgroundColor: '#4caf50',
    padding: 15,
    borderRadius: 50,
  },
  captureText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  imagePreview: {
    marginHorizontal: 20,
    marginBottom: 20,
  },
  previewImage: {
    width: '100%',
    height: 200,
    borderRadius: 10,
  },
  inputContainer: {
    marginHorizontal: 20,
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    minHeight: 80,
    backgroundColor: 'white',
  },
  submitButton: {
    backgroundColor: '#4caf50',
    marginHorizontal: 20,
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 20,
  },
  disabledButton: {
    backgroundColor: '#cccccc',
  },
  submitText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  resultContainer: {
    marginHorizontal: 20,
    padding: 15,
    backgroundColor: 'white',
    borderRadius: 8,
    marginBottom: 20,
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#2e7d32',
  },
});

export default ICHSMobileApp;
