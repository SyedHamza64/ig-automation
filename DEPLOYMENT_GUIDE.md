# IG Automation - Deployment Guide

## 🚀 Overview

This guide ensures your IG Automation system is production-ready and won't encounter the issues we just fixed.

## 🔧 Issues Fixed

### 1. **Database Schema Mismatch**

- **Problem**: Code models didn't match database schema
- **Solution**: Added automatic database health checks on startup
- **Prevention**: System now validates schema on every startup

### 2. **JWT Token Expiration**

- **Problem**: Hardcoded JWT tokens expired, breaking authentication
- **Solution**: Automatic token renewal with expiration checking
- **Prevention**: Tokens are automatically refreshed when needed

### 3. **Hardcoded Configuration**

- **Problem**: URLs, credentials, and settings were hardcoded
- **Solution**: Dynamic configuration from environment variables
- **Prevention**: All settings are now configurable via environment

### 4. **Poor Error Handling**

- **Problem**: Generic error messages, no user feedback
- **Solution**: Comprehensive error handling with user-friendly messages
- **Prevention**: Toast notifications and retry mechanisms

## 📋 Pre-Deployment Checklist

### Backend Configuration

1. **Environment Variables** (create `backend/.env`):

```env
# Database
POSTGRES_DB=ig_automation
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Security
SECRET_KEY=your_very_secure_secret_key_here

# Application
APP_PORT=8000
TZ=Asia/Karachi

# External Services
ADSPOWER_BASE_URL=http://127.0.0.1:50325
BULKCREATE_SERVER_URL=http://127.0.0.1:4000

# Authentication
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
JWT_ALGORITHM=HS256

# Default Admin (change these!)
DEFAULT_ADMIN_EMAIL=admin@yourcompany.com
DEFAULT_ADMIN_PASSWORD=your_secure_admin_password

# CORS (add your domain)
CORS_ORIGINS=["http://localhost:5173","https://yourdomain.com"]

# Features
ENABLE_DATABASE_HEALTH_CHECK=true
ENABLE_AUTO_LOGIN=true
ENABLE_DEBUG_MODE=false
```

2. **Database Setup**:

```bash
# Create database
createdb ig_automation

# Run migrations
cd backend
python -m alembic upgrade head
```

### Frontend Configuration

1. **Environment Variables** (create `frontend/.env`):

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_BULKCREATE_SERVER_URL=http://localhost:4000

# Default Admin Credentials (same as backend)
VITE_DEFAULT_ADMIN_EMAIL=admin@yourcompany.com
VITE_DEFAULT_ADMIN_PASSWORD=your_secure_admin_password

# Development (remove in production)
VITE_DEV_JWT=your_jwt_token_here
VITE_DEV_EMAIL=admin@yourcompany.com
VITE_DEV_PASSWORD=your_secure_admin_password
```

## 🚀 Deployment Steps

### 1. Backend Deployment

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run database migrations
python -m alembic upgrade head

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend Deployment

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Serve the built files
npm run preview
```

### 3. Bulkcreate Services

```bash
cd bulkcreate-main/bulkcreate-main

# Server
cd server
npm install
npm run dev

# Client (in another terminal)
cd client
npm install
npm run dev
```

## 🔍 Health Checks

### Automatic Checks

- ✅ Database schema validation on startup
- ✅ JWT token expiration checking
- ✅ API connectivity validation
- ✅ Error logging and monitoring

### Manual Checks

1. **Backend Health**: `GET http://localhost:8000/health`
2. **Database**: Check startup logs for schema validation
3. **Authentication**: Try logging in through the frontend
4. **Profile Linking**: Test the profile linking functionality

## 🛡️ Security Considerations

### Production Security

1. **Change Default Passwords**: Update all default credentials
2. **Use HTTPS**: Configure SSL certificates
3. **Environment Variables**: Never commit `.env` files
4. **Database Security**: Use strong passwords and restrict access
5. **CORS Configuration**: Only allow your domain

### Monitoring

- Check application logs regularly
- Monitor database performance
- Set up alerts for authentication failures
- Monitor API response times

## 🔧 Troubleshooting

### Common Issues

1. **"Database schema validation failed"**

   - Run: `python -m alembic upgrade head`
   - Check database connection

2. **"Authentication failed"**

   - Check JWT token expiration
   - Verify admin credentials
   - Check SECRET_KEY configuration

3. **"Profile linking not working"**

   - Verify database schema is up to date
   - Check bulkcreate server is running
   - Verify CORS configuration

4. **"Network errors"**
   - Check all services are running
   - Verify URLs in configuration
   - Check firewall settings

### Log Files

- Backend logs: Console output or `app.log`
- Frontend errors: Browser console
- Database logs: PostgreSQL logs

## 📞 Support

If you encounter issues:

1. Check the logs first
2. Verify all environment variables are set
3. Ensure all services are running
4. Check the health endpoints

## 🔄 Updates and Maintenance

### Regular Maintenance

1. **Update Dependencies**: Monthly security updates
2. **Database Backups**: Daily automated backups
3. **Log Rotation**: Configure log rotation
4. **Monitor Performance**: Check response times

### Updating the System

1. Pull latest code
2. Update environment variables if needed
3. Run database migrations: `python -m alembic upgrade head`
4. Restart all services
5. Verify health checks pass

---

## ✅ Production Readiness Checklist

- [ ] All environment variables configured
- [ ] Database created and migrated
- [ ] Default passwords changed
- [ ] HTTPS configured (if applicable)
- [ ] CORS properly configured
- [ ] Health checks passing
- [ ] All services running
- [ ] Error handling working
- [ ] Authentication working
- [ ] Profile linking working
- [ ] Monitoring set up
- [ ] Backups configured

Your system is now production-ready! 🎉
