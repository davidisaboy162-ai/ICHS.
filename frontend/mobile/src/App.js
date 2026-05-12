import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Image,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import * as Location from 'expo-location';
import { StatusBar as ExpoStatusBar } from 'expo-status-bar';
import { API_BASE_URL, fetchNearbyAlerts, fetchWeatherRisk, submitCombinedDiagnosis } from './api';

const theme = {
  bg: '#f4f1e8',
  panel: '#ffffff',
  panelSoft: '#f8f5ed',
  panelWarm: '#f2ead6',
  text: '#1f2f1f',
  muted: '#647062',
  leaf: '#4d7a42',
  leafDark: '#355930',
  soil: '#7c5734',
  sun: '#d8a13d',
  line: '#d9decf',
  danger: '#b65454',
  success: '#587d46',
  sky: '#dcecf0',
};

const emptyResult = {
  disease_name: null,
  confidence: 0,
  input_type: '',
  alerts_count: 0,
  weather_risk: null,
  created_at: '',
};

function formatConfidence(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return '0%';
  }
  return `${Math.round(number * 100)}%`;
}

function formatCoordinate(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return '';
  }
  return number.toFixed(6);
}

function buildImagePayload(asset) {
  if (!asset?.uri) {
    return null;
  }

  return {
    uri: asset.uri,
    name: asset.fileName || `crop-${Date.now()}.jpg`,
    type: asset.mimeType || 'image/jpeg',
  };
}

function useRequestPermissions() {
  const [cameraPermission, setCameraPermission] = useState(null);
  const [libraryPermission, setLibraryPermission] = useState(null);
  const [locationPermission, setLocationPermission] = useState(null);
  const [locationServicesEnabled, setLocationServicesEnabled] = useState(null);

  const requestAll = async () => {
    const camera = await ImagePicker.requestCameraPermissionsAsync();
    setCameraPermission(camera.status === 'granted');

    const library = await ImagePicker.requestMediaLibraryPermissionsAsync();
    setLibraryPermission(library.status === 'granted');

    const servicesEnabled = await Location.hasServicesEnabledAsync();
    setLocationServicesEnabled(servicesEnabled);

    const location = await Location.requestForegroundPermissionsAsync();
    setLocationPermission(location.status === 'granted');
  };

  useEffect(() => {
    requestAll().catch(() => {
      setCameraPermission(false);
      setLibraryPermission(false);
      setLocationPermission(false);
      setLocationServicesEnabled(false);
    });
  }, []);

  return {
    cameraPermission,
    libraryPermission,
    locationPermission,
    locationServicesEnabled,
    requestAll,
    setLocationPermission,
    setLocationServicesEnabled,
    setCameraPermission,
    setLibraryPermission,
  };
}

export default function App() {
  const {
    cameraPermission,
    libraryPermission,
    locationPermission,
    locationServicesEnabled,
    requestAll,
    setLocationPermission,
    setLocationServicesEnabled,
    setCameraPermission,
    setLibraryPermission,
  } = useRequestPermissions();

  const [image, setImage] = useState(null);
  const [symptoms, setSymptoms] = useState('');
  const [locationLabel, setLocationLabel] = useState('Field location');
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [status, setStatus] = useState('Ready when you are.');
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(emptyResult);
  const [weather, setWeather] = useState(null);
  const [nearbyAlerts, setNearbyAlerts] = useState([]);
  const [lastError, setLastError] = useState('');

  const apiLabel = useMemo(() => API_BASE_URL.replace(/^https?:\/\//, ''), []);

  const requestDeviceLocation = async () => {
    try {
      const servicesEnabled = await Location.hasServicesEnabledAsync();
      setLocationServicesEnabled(servicesEnabled);
      if (!servicesEnabled) {
        setStatus('Location services are off on this device.');
        return;
      }

      const permission = await Location.requestForegroundPermissionsAsync();
      const granted = permission.status === 'granted';
      setLocationPermission(granted);
      if (!granted) {
        setStatus('Location permission denied. You can type coordinates manually.');
        return;
      }

      const coords = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });
      setLatitude(String(coords.coords.latitude));
      setLongitude(String(coords.coords.longitude));
      setLocationLabel('Current field');
      setStatus('Location captured from device.');
    } catch (error) {
      setStatus('Could not read device location.');
    }
  };

  const pickImage = async (source) => {
    try {
      if (source === 'camera') {
        const permission = await ImagePicker.requestCameraPermissionsAsync();
        setCameraPermission(permission.status === 'granted');
        if (permission.status !== 'granted') {
          setStatus('Camera permission denied.');
          return;
        }

        const response = await ImagePicker.launchCameraAsync({
          quality: 0.85,
          allowsEditing: true,
          aspect: [4, 3],
        });

        if (!response.canceled && response.assets?.[0]) {
          setImage(buildImagePayload(response.assets[0]));
          setStatus('Image captured.');
        }
        return;
      }

      const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      setLibraryPermission(permission.status === 'granted');
      if (permission.status !== 'granted') {
        setStatus('Gallery permission denied.');
        return;
      }

      const response = await ImagePicker.launchImageLibraryAsync({
        quality: 0.85,
        allowsEditing: true,
        aspect: [4, 3],
      });

      if (!response.canceled && response.assets?.[0]) {
        setImage(buildImagePayload(response.assets[0]));
        setStatus('Image selected.');
      }
    } catch (error) {
      setStatus('Could not open image picker.');
    }
  };

  const submit = async () => {
    const hasImage = Boolean(image?.uri);
    const trimmedSymptoms = symptoms.trim();

    if (!hasImage && !trimmedSymptoms) {
      Alert.alert('Missing input', 'Add a crop photo, symptom text, or both.');
      return;
    }

    const lat = latitude.trim() ? Number(latitude) : 0;
    const lon = longitude.trim() ? Number(longitude) : 0;

    if ((latitude.trim() && !Number.isFinite(lat)) || (longitude.trim() && !Number.isFinite(lon))) {
      Alert.alert('Invalid coordinates', 'Latitude and longitude must be valid numbers.');
      return;
    }

    setSubmitting(true);
    setLastError('');
    setStatus('Sending diagnosis to backend...');

    try {
      const diagnosis = await submitCombinedDiagnosis({
        image: hasImage ? image : null,
        symptoms: trimmedSymptoms,
        latitude: lat,
        longitude: lon,
        locationName: locationLabel.trim(),
      });

      setResult({
        ...emptyResult,
        ...diagnosis,
      });
      setWeather(diagnosis.weather_risk || null);
      setStatus('Diagnosis complete.');

      if (Number.isFinite(lat) && Number.isFinite(lon)) {
        const [weatherRisk, alerts] = await Promise.all([
          fetchWeatherRisk({
            latitude: lat,
            longitude: lon,
            locationName: locationLabel.trim(),
          }).catch(() => null),
          fetchNearbyAlerts({
            latitude: lat,
            longitude: lon,
            radius: 10,
          }).catch(() => null),
        ]);

        if (weatherRisk) {
          setWeather({
            risk_level: weatherRisk.risk_level,
            risk_score: weatherRisk.risk_score,
            explanation: weatherRisk.explanation,
            weather: weatherRisk.weather,
          });
        }

        if (alerts?.results) {
          setNearbyAlerts(alerts.results);
        }
      }
    } catch (error) {
      setLastError(error.message || 'Diagnosis failed.');
      setStatus('Something went wrong.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ExpoStatusBar style="light" />
      <StatusBar barStyle="light-content" backgroundColor={theme.leafDark} />
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
          <View style={styles.hero}>
            <View style={styles.badgeRow}>
              <View style={styles.badge}>
                <Text style={styles.badgeText}>ICHS MOBILE</Text>
              </View>
              <View style={styles.badgeMuted}>
                <Text style={styles.badgeMutedText}>{status}</Text>
              </View>
            </View>

            <Text style={styles.title}>Crop diagnosis that works in the field.</Text>
            <Text style={styles.subtitle}>
              Capture a photo, describe the symptoms, add location details, and send everything
              to the backend in one clean flow.
            </Text>

            <View style={styles.apiBox}>
              <Text style={styles.apiLabel}>Backend</Text>
              <Text style={styles.apiValue}>{apiLabel}</Text>
            </View>

            <View style={styles.permissionRow}>
              <PermissionPill label="Camera" granted={cameraPermission} />
              <PermissionPill label="Gallery" granted={libraryPermission} />
              <PermissionPill
                label="Location"
                granted={locationPermission && locationServicesEnabled}
              />
            </View>
          </View>

          <View style={styles.card}>
            <SectionTitle title="Image" subtitle="Use the camera or choose from your gallery." />
            <View style={styles.actionRow}>
              <ActionButton label="Take Photo" onPress={() => pickImage('camera')} />
              <ActionButton label="Pick Image" variant="secondary" onPress={() => pickImage('library')} />
            </View>

            <View style={styles.preview}>
              {image?.uri ? (
                <Image source={{ uri: image.uri }} style={styles.previewImage} />
              ) : (
                <View style={styles.previewEmpty}>
                  <Text style={styles.previewEmptyText}>No crop image selected yet.</Text>
                </View>
              )}
            </View>
          </View>

          <View style={styles.card}>
            <SectionTitle title="Symptoms" subtitle="Add details about the crop, leaves, and changes you see." />
            <TextInput
              style={styles.textArea}
              value={symptoms}
              onChangeText={setSymptoms}
              multiline
              placeholder="Example: yellowing edges, brown spots, curling leaves, powdery residue..."
              placeholderTextColor="#93a08f"
              textAlignVertical="top"
            />
          </View>

          <View style={styles.card}>
            <SectionTitle title="Location" subtitle="GPS helps weather risk and nearby alert matching." />

            <View style={styles.actionRow}>
              <ActionButton label="Use Device Location" onPress={requestDeviceLocation} />
              <ActionButton label="Refresh Permissions" variant="secondary" onPress={requestAll} />
            </View>

            <View style={styles.inputGrid}>
              <Field
                label="Field name"
                value={locationLabel}
                onChangeText={setLocationLabel}
                placeholder="North paddock"
              />
              <Field
                label="Latitude"
                value={latitude}
                onChangeText={setLatitude}
                placeholder="e.g. 6.5244"
                keyboardType="decimal-pad"
              />
              <Field
                label="Longitude"
                value={longitude}
                onChangeText={setLongitude}
                placeholder="e.g. 3.3792"
                keyboardType="decimal-pad"
              />
            </View>

            <Text style={styles.helper}>
              If location permission is denied, enter coordinates manually and the app will still
              diagnose.
            </Text>
          </View>

          <TouchableOpacity
            activeOpacity={0.9}
            style={[styles.submit, submitting && styles.submitDisabled]}
            onPress={submit}
            disabled={submitting}
          >
            <Text style={styles.submitText}>{submitting ? 'Running diagnosis...' : 'Run Diagnosis'}</Text>
          </TouchableOpacity>

          {lastError ? (
            <View style={styles.errorBox}>
              <Text style={styles.errorTitle}>Request failed</Text>
              <Text style={styles.errorText}>{lastError}</Text>
            </View>
          ) : null}

          <View style={styles.card}>
            <SectionTitle title="Result" subtitle="The backend prediction, confidence, and metadata." />

            <View style={styles.resultTop}>
              <View style={styles.resultLeft}>
                <Text style={styles.resultDisease}>{result.disease_name || 'No diagnosis yet'}</Text>
                <Text style={styles.resultMeta}>
                  {result.input_type ? result.input_type.toUpperCase() : 'Awaiting input'}
                </Text>
              </View>
              <View style={styles.confidencePill}>
                <Text style={styles.confidenceText}>{formatConfidence(result.confidence)}</Text>
              </View>
            </View>

            <View style={styles.infoGrid}>
              <InfoChip label="Alerts" value={`${result.alerts_count || 0}`} />
              <InfoChip label="Created" value={result.created_at ? new Date(result.created_at).toLocaleString() : '—'} />
            </View>
          </View>

          <View style={styles.card}>
            <SectionTitle title="Weather risk" subtitle="Weather conditions returned by the backend." />
            {weather ? (
              <View style={styles.weatherBox}>
                <Text style={styles.weatherLevel}>{weather.risk_level || 'Unknown'}</Text>
                <Text style={styles.weatherScore}>Score {weather.risk_score ?? '—'}</Text>
                <Text style={styles.weatherText}>{weather.explanation || 'No explanation available.'}</Text>
              </View>
            ) : (
              <Text style={styles.emptyNote}>Weather risk will appear after a diagnosis with coordinates.</Text>
            )}
          </View>

          <View style={styles.card}>
            <SectionTitle title="Nearby alerts" subtitle="Recent outbreaks near the submitted coordinates." />
            {nearbyAlerts.length > 0 ? (
              nearbyAlerts.map((item, index) => (
                <View key={`${item.id || item.report_id || index}`} style={styles.alertItem}>
                  <Text style={styles.alertTitle}>
                    {item.disease || item.disease_name || item.predicted_disease || 'Unknown disease'}
                  </Text>
                  <Text style={styles.alertMeta}>
                    Confidence {formatConfidence(item.confidence)} • Lat {formatCoordinate(item.latitude)} • Lon{' '}
                    {formatCoordinate(item.longitude)}
                  </Text>
                </View>
              ))
            ) : (
              <Text style={styles.emptyNote}>No nearby alerts yet, or location has not been set.</Text>
            )}
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function SectionTitle({ title, subtitle }) {
  return (
    <View style={styles.sectionHeader}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <Text style={styles.sectionSubtitle}>{subtitle}</Text>
    </View>
  );
}

function PermissionPill({ label, granted }) {
  const state = granted === null ? 'pending' : granted ? 'granted' : 'denied';
  const palette =
    state === 'granted'
      ? styles.permissionGranted
      : state === 'denied'
        ? styles.permissionDenied
        : styles.permissionPending;

  return (
    <View style={[styles.permissionPill, palette]}>
      <Text style={styles.permissionLabel}>{label}</Text>
      <Text style={styles.permissionState}>{state}</Text>
    </View>
  );
}

function ActionButton({ label, onPress, variant = 'primary' }) {
  return (
    <TouchableOpacity
      activeOpacity={0.9}
      onPress={onPress}
      style={[styles.actionButton, variant === 'secondary' && styles.actionButtonSecondary]}
    >
      <Text style={[styles.actionButtonText, variant === 'secondary' && styles.actionButtonTextSecondary]}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

function Field({ label, value, onChangeText, placeholder, keyboardType = 'default' }) {
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        style={styles.fieldInput}
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor="#9aa294"
        keyboardType={keyboardType}
      />
    </View>
  );
}

function InfoChip({ label, value }) {
  return (
    <View style={styles.infoChip}>
      <Text style={styles.infoChipLabel}>{label}</Text>
      <Text style={styles.infoChipValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: theme.bg,
  },
  flex: {
    flex: 1,
  },
  scroll: {
    paddingBottom: 36,
    backgroundColor: theme.bg,
  },
  hero: {
    backgroundColor: theme.leafDark,
    paddingHorizontal: 20,
    paddingTop: 28,
    paddingBottom: 24,
    borderBottomLeftRadius: 28,
    borderBottomRightRadius: 28,
  },
  badgeRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 16,
  },
  badge: {
    backgroundColor: 'rgba(255,255,255,0.12)',
    borderColor: 'rgba(255,255,255,0.16)',
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  badgeText: {
    color: '#f3f1e6',
    letterSpacing: 1.2,
    fontSize: 11,
    fontWeight: '700',
  },
  badgeMuted: {
    backgroundColor: 'rgba(216,161,61,0.16)',
    borderColor: 'rgba(216,161,61,0.35)',
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  badgeMutedText: {
    color: '#f7e5b8',
    fontSize: 11,
    fontWeight: '600',
  },
  title: {
    fontSize: 34,
    lineHeight: 40,
    color: '#fffdf6',
    fontWeight: '800',
    maxWidth: 520,
  },
  subtitle: {
    marginTop: 12,
    color: 'rgba(255,255,255,0.86)',
    fontSize: 16,
    lineHeight: 24,
    maxWidth: 560,
  },
  apiBox: {
    marginTop: 18,
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderColor: 'rgba(255,255,255,0.14)',
    borderWidth: 1,
    borderRadius: 18,
    padding: 14,
  },
  apiLabel: {
    color: 'rgba(255,255,255,0.72)',
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  apiValue: {
    marginTop: 4,
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
  },
  permissionRow: {
    marginTop: 16,
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  permissionPill: {
    minWidth: 98,
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderWidth: 1,
  },
  permissionGranted: {
    backgroundColor: 'rgba(112, 163, 96, 0.18)',
    borderColor: 'rgba(112, 163, 96, 0.32)',
  },
  permissionDenied: {
    backgroundColor: 'rgba(181, 84, 84, 0.15)',
    borderColor: 'rgba(181, 84, 84, 0.28)',
  },
  permissionPending: {
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderColor: 'rgba(255,255,255,0.14)',
  },
  permissionLabel: {
    color: '#f4f0e6',
    fontSize: 12,
    fontWeight: '700',
  },
  permissionState: {
    marginTop: 4,
    color: 'rgba(255,255,255,0.8)',
    fontSize: 12,
    textTransform: 'capitalize',
  },
  card: {
    marginTop: 16,
    marginHorizontal: 16,
    backgroundColor: theme.panel,
    borderRadius: 24,
    padding: 18,
    borderWidth: 1,
    borderColor: theme.line,
    shadowColor: '#2b3b28',
    shadowOpacity: 0.06,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 8 },
    elevation: 3,
  },
  sectionHeader: {
    marginBottom: 14,
  },
  sectionTitle: {
    color: theme.text,
    fontSize: 20,
    fontWeight: '800',
  },
  sectionSubtitle: {
    marginTop: 4,
    color: theme.muted,
    fontSize: 13,
    lineHeight: 19,
  },
  actionRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 14,
  },
  actionButton: {
    flexGrow: 1,
    flexBasis: 0,
    minWidth: 120,
    backgroundColor: theme.leaf,
    borderRadius: 16,
    paddingVertical: 14,
    paddingHorizontal: 14,
    alignItems: 'center',
  },
  actionButtonSecondary: {
    backgroundColor: theme.panelSoft,
    borderWidth: 1,
    borderColor: theme.line,
  },
  actionButtonText: {
    color: '#fff',
    fontWeight: '800',
    fontSize: 14,
  },
  actionButtonTextSecondary: {
    color: theme.text,
  },
  preview: {
    borderRadius: 20,
    overflow: 'hidden',
    backgroundColor: theme.panelSoft,
    borderWidth: 1,
    borderColor: theme.line,
    minHeight: 210,
  },
  previewImage: {
    width: '100%',
    height: 260,
  },
  previewEmpty: {
    minHeight: 210,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  previewEmptyText: {
    color: theme.muted,
    fontSize: 14,
  },
  textArea: {
    minHeight: 150,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: theme.line,
    backgroundColor: theme.panelSoft,
    paddingHorizontal: 14,
    paddingVertical: 14,
    color: theme.text,
    fontSize: 15,
    lineHeight: 22,
  },
  inputGrid: {
    gap: 12,
  },
  field: {
    gap: 6,
  },
  fieldLabel: {
    color: theme.text,
    fontWeight: '700',
    fontSize: 13,
  },
  fieldInput: {
    borderRadius: 16,
    borderWidth: 1,
    borderColor: theme.line,
    backgroundColor: theme.panelSoft,
    paddingHorizontal: 14,
    paddingVertical: 13,
    color: theme.text,
    fontSize: 15,
  },
  helper: {
    marginTop: 12,
    color: theme.muted,
    fontSize: 12,
    lineHeight: 18,
  },
  submit: {
    marginHorizontal: 16,
    marginTop: 16,
    backgroundColor: theme.soil,
    borderRadius: 18,
    paddingVertical: 16,
    alignItems: 'center',
    shadowColor: '#7c5734',
    shadowOpacity: 0.2,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 6 },
    elevation: 2,
  },
  submitDisabled: {
    opacity: 0.7,
  },
  submitText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '800',
  },
  errorBox: {
    marginHorizontal: 16,
    marginTop: 14,
    backgroundColor: 'rgba(181,84,84,0.12)',
    borderColor: 'rgba(181,84,84,0.24)',
    borderWidth: 1,
    borderRadius: 18,
    padding: 14,
  },
  errorTitle: {
    color: theme.danger,
    fontWeight: '800',
    fontSize: 14,
  },
  errorText: {
    marginTop: 4,
    color: theme.text,
    fontSize: 13,
    lineHeight: 18,
  },
  resultTop: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 12,
    marginBottom: 12,
  },
  resultLeft: {
    flex: 1,
  },
  resultDisease: {
    color: theme.text,
    fontSize: 22,
    fontWeight: '800',
  },
  resultMeta: {
    marginTop: 4,
    color: theme.muted,
    fontSize: 12,
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  confidencePill: {
    borderRadius: 999,
    backgroundColor: 'rgba(77, 122, 66, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(77, 122, 66, 0.24)',
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  confidenceText: {
    color: theme.leafDark,
    fontWeight: '800',
  },
  infoGrid: {
    flexDirection: 'row',
    gap: 12,
    flexWrap: 'wrap',
  },
  infoChip: {
    flexGrow: 1,
    flexBasis: 0,
    minWidth: 130,
    padding: 12,
    borderRadius: 16,
    backgroundColor: theme.panelSoft,
    borderWidth: 1,
    borderColor: theme.line,
  },
  infoChipLabel: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.6,
  },
  infoChipValue: {
    marginTop: 6,
    color: theme.text,
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '600',
  },
  weatherBox: {
    borderRadius: 18,
    backgroundColor: theme.panelSoft,
    borderWidth: 1,
    borderColor: theme.line,
    padding: 14,
  },
  weatherLevel: {
    color: theme.leafDark,
    fontSize: 20,
    fontWeight: '800',
    textTransform: 'capitalize',
  },
  weatherScore: {
    marginTop: 4,
    color: theme.soil,
    fontSize: 13,
    fontWeight: '700',
  },
  weatherText: {
    marginTop: 8,
    color: theme.text,
    lineHeight: 20,
    fontSize: 13,
  },
  emptyNote: {
    color: theme.muted,
    fontSize: 13,
    lineHeight: 19,
  },
  alertItem: {
    borderRadius: 16,
    backgroundColor: theme.panelSoft,
    borderWidth: 1,
    borderColor: theme.line,
    padding: 12,
    marginBottom: 10,
  },
  alertTitle: {
    color: theme.text,
    fontWeight: '800',
    fontSize: 14,
  },
  alertMeta: {
    marginTop: 4,
    color: theme.muted,
    fontSize: 12,
    lineHeight: 18,
  },
});
