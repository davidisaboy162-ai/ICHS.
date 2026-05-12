import { Platform } from 'react-native';

const stripTrailingSlash = (value) => value.replace(/\/+$/, '');

const inferBaseUrl = () => {
  const explicit = process.env.EXPO_PUBLIC_API_BASE_URL?.trim();
  if (explicit) {
    return stripTrailingSlash(explicit);
  }

  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000/api/v1';
  }

  return 'http://localhost:8000/api/v1';
};

export const API_BASE_URL = inferBaseUrl();

const buildUrl = (path, params = null) => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const query = params
    ? Object.entries(params)
        .filter(([, value]) => value !== undefined && value !== null && `${value}`.length > 0)
        .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
        .join('&')
    : '';

  return `${API_BASE_URL}${normalizedPath}${query ? `?${query}` : ''}`;
};

const parseJson = async (response) => {
  const text = await response.text();
  if (!text) {
    return {};
  }

  try {
    return JSON.parse(text);
  } catch (error) {
    return { raw: text };
  }
};

export async function submitCombinedDiagnosis({
  image,
  symptoms,
  latitude,
  longitude,
  locationName,
}) {
  const formData = new FormData();

  if (image?.uri) {
    formData.append('file', {
      uri: image.uri,
      name: image.name || `crop-${Date.now()}.jpg`,
      type: image.type || 'image/jpeg',
    });
  }

  if (symptoms?.trim()) {
    formData.append('symptoms', symptoms.trim());
  }

  formData.append('latitude', String(latitude ?? 0));
  formData.append('longitude', String(longitude ?? 0));
  formData.append('location_name', locationName?.trim() || '');

  const response = await fetch(buildUrl('/diagnosis/combined/'), {
    method: 'POST',
    body: formData,
  });

  const data = await parseJson(response);
  if (!response.ok) {
    throw new Error(data.detail || data.error || 'Diagnosis failed.');
  }

  return data;
}

export async function fetchWeatherRisk({ latitude, longitude, locationName }) {
  const response = await fetch(buildUrl('/weather/risk/'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      latitude,
      longitude,
      location_name: locationName || '',
    }),
  });

  const data = await parseJson(response);
  if (!response.ok) {
    throw new Error(data.detail || data.error || 'Weather check failed.');
  }

  return data;
}

export async function fetchNearbyAlerts({ latitude, longitude, radius = 10 }) {
  const response = await fetch(
    buildUrl('/alerts/', {
      latitude,
      longitude,
      radius,
    }),
  );

  const data = await parseJson(response);
  if (!response.ok) {
    throw new Error(data.detail || data.error || 'Could not load nearby alerts.');
  }

  return data;
}
