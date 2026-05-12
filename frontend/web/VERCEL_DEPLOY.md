# Vercel Deployment Guide for ICHS Frontend

## Prerequisites
- A Vercel account (sign up at https://vercel.com)
- Your backend API deployed and accessible (e.g., on Railway, Render, Heroku, or another hosting platform)

## Quick Deploy (Recommended)

### Option 1: Vercel CLI (Fastest)
```bash
# Install Vercel CLI globally
npm i -g vercel

# Navigate to frontend directory
cd frontend/web

# Login to Vercel
vercel login

# Deploy (follow prompts)
vercel
```

### Option 2: Git Integration (CI/CD)
1. Push your code to GitHub
2. Go to https://vercel.com and click "Add New Project"
3. Import your GitHub repository
4. Configure the project:
   - Framework Preset: Create React App
   - Build Command: `npm run build` (or leave blank)
   - Output Directory: `build` (or leave blank)
5. Add environment variable:
   - Key: `REACT_APP_API_BASE_URL`
   - Value: Your deployed backend URL (e.g., `https://your-backend.railway.app/api/v1`)
6. Click "Deploy"

## Configuration Files Created

### vercel.json
```json
{
  "buildCommand": "npm run build",
  "devCommand": "npm start",
  "installCommand": "npm install",
  "framework": "create-react-app",
  "outputDirectory": "build"
}
```

### .env.production
```
REACT_APP_API_BASE_URL=https://your-backend-url.com/api/v1
```

## Important: Update Your Backend URL

Before deploying, update the `REACT_APP_API_BASE_URL` in either:
1. Vercel Dashboard → Project Settings → Environment Variables
2. Or edit `frontend/web/.env.production` before deploying

Replace `https://your-backend-url.com/api/v1` with your actual backend URL.

## Backend Deployment Options

Since the frontend needs a backend API, you'll need to deploy your Django backend separately. Recommended options:

| Platform | Free Tier | URL Format |
|----------|-----------|------------|
| Railway | $5/month | `https://your-app.railway.app` |
| Render | Free (sleeps) | `https://your-app.onrender.com` |
| Heroku | Free (sleeps) | `https://your-app.herokuapp.com` |
| PythonAnywhere | Free | `https://your-user.pythonanywhere.com` |

## Post-Deployment Checklist

- [ ] Frontend loads without errors
- [ ] API calls reach your backend
- [ ] Image upload works
- [ ] Location services work (HTTPS required)
- [ ] All features function correctly

## Troubleshooting

### CORS Errors
If you get CORS errors, ensure your Django backend has:
```python
# In settings.py
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend.vercel.app",
]
```

### API Not Found
- Verify `REACT_APP_API_BASE_URL` is set correctly in Vercel
- Ensure your backend is running and accessible
- Check that your backend URL ends with `/api/v1`

### Build Errors
- Ensure all dependencies are in package.json
- Run `npm run build` locally first to test