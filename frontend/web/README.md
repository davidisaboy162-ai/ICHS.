# ICHS Web Frontend Setup

## Prerequisites
- Node.js (v16 or higher)
- npm or yarn

## Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend/web
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## Features

- **Crop Disease Diagnosis**: Upload images or describe symptoms
- **Interactive Map**: View disease outbreaks and alerts
- **Real-time Alerts**: Get notifications about nearby outbreaks
- **Responsive Design**: Works on desktop and mobile devices
- **Agricultural Theme**: Nature-inspired color scheme and icons

## Backend Integration

The frontend connects to the FastAPI backend running on `http://localhost:8000`.

Make sure the backend is running before using the diagnosis features.

## Technologies Used

- React 18
- React Bootstrap
- Leaflet Maps
- React Icons
- CSS3 with custom properties

## Building for Production

```bash
npm run build
```

This builds the app for production to the `build` folder.

## Available Scripts

- `npm start` - Runs the app in development mode
- `npm test` - Launches the test runner
- `npm run build` - Builds the app for production
- `npm run eject` - Ejects from Create React App (irreversible)

## Troubleshooting

### Map not loading
- Check that Leaflet CSS is properly imported
- Ensure you have a stable internet connection for tile loading

### API connection issues
- Verify the backend is running on port 8000
- Check CORS settings in the backend

### Mobile responsiveness
- Test on different screen sizes
- Use browser dev tools for mobile simulation