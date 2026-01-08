# Disney Omni-Tracker - Render.com Deployment Guide

## Overview
Deploy the Disney World Wait Time Tracker with AI predictions to Render.com for production hosting.

## Prerequisites
- GitHub account with this code pushed to a repository
- Render.com account (free tier available)
- Optional: PostgreSQL database (Render provides free PostgreSQL)

## Step 1: Create GitHub Repository
1. Create a new repository on GitHub
2. Push all project files to the repository:
   ```bash
   git init
   git add .
   git commit -m "Initial deployment setup"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

## Step 2: Deploy to Render.com
1. Go to [Render.com](https://render.com) and sign up/login
2. Click **"New +"** → **"Web Service"**
3. **Connect GitHub**: Authorize Render to access your GitHub account
4. **Select Repository**: Choose the Disney Omni-Tracker repository
5. **Configure Service**:
   - **Name**: disney-omni-tracker (or your preferred name)
   - **Environment**: Python 3
   - **Region**: Choose closest to your users
   - **Branch**: main

## Step 3: Build Configuration
Set the following configuration in Render:

### Build Command
```
pip install -r requirements.txt
```

### Start Command
```
bash start.sh
```

### Environment Variables (Optional)
If using PostgreSQL:
- **Key**: `DATABASE_URL`
- **Value**: Your PostgreSQL connection string (Render provides this)

## Step 4: Deploy
1. Click **"Create Web Service"**
2. Wait for deployment (typically 2-5 minutes)
3. Your app will be available at: `https://your-service-name.onrender.com`

## Features After Deployment
- **Real-time Dashboard**: Interactive wait time visualization
- **AI Predictions**: Machine learning recommendations for each ride
- **Automatic Updates**: Scheduler runs every 15 minutes
- **Mobile Optimized**: Responsive tile grid layout
- **API Endpoints**: REST API for external integrations

## Monitoring
- **Logs**: Available in Render dashboard
- **Health Check**: Visit `/health` endpoint (if implemented)
- **Database**: Monitor PostgreSQL usage in Render dashboard

## Troubleshooting
- **Build Fails**: Check requirements.txt for correct dependencies
- **App Crashes**: Review Render logs for error messages
- **Database Issues**: Verify DATABASE_URL environment variable
- **Scheduler Not Running**: Check that background processes are allowed

## Local Development
To run locally:
```bash
# Install dependencies
pip install -r requirements.txt

# Run scheduler and dashboard
bash start.sh
```

## Support
For issues:
1. Check Render logs
2. Verify environment variables
3. Ensure all dependencies are in requirements.txt
4. Test locally before deploying

## Production Considerations
- **Free Tier**: Render free tier has usage limits
- **Database**: Consider PostgreSQL for production data persistence
- **Scaling**: Upgrade plan for higher traffic
- **Monitoring**: Set up alerts for downtime
