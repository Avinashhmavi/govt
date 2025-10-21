# 🚀 Northflank Deployment Guide

## Quick Start Steps

### 1. **Sign up for Northflank**
- Go to [https://northflank.com/](https://northflank.com/)
- Click "Get started" and create your account
- Choose the free tier to start

### 2. **Create New Project**
- In Northflank dashboard, click "New Project"
- Name it: `govt-directory`
- Choose "Deploy from Git"

### 3. **Connect GitHub Repository**
- Repository: `Avinashhmavi/govt`
- Branch: `neodb`
- Build context: Root directory

### 4. **Configure Service**
- **Service Name**: `govt-directory`
- **Port**: `5000`
- **Dockerfile**: Use the provided Dockerfile

### 5. **Set Environment Variables**
Copy these into Northflank's environment section:

```bash
DB_HOST=ep-steep-band-adymw02q-pooler.c-2.us-east-1.aws.neon.tech
DB_PORT=5432
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=npg_zJ5YA8akldbi
DB_SSLMODE=require
DB_CHANNEL_BINDING=require
FLASK_ENV=production
SECRET_KEY=your-secure-secret-key-here
PORT=5000
OPENAI_API_KEY=your_openai_api_key_here
```

### 6. **Configure Resources**
- **CPU**: 0.5 vCPU (minimum)
- **Memory**: 1GB RAM
- **Storage**: 2GB

### 7. **Deploy**
- Click "Deploy"
- Wait for build to complete (5-10 minutes)
- Your app will be available at the provided URL

## 🎯 What You Get

✅ **Automatic deployments** from Git pushes  
✅ **SSL certificates** included  
✅ **Health monitoring** and auto-restart  
✅ **Logs and metrics** dashboard  
✅ **Easy scaling** options  
✅ **Custom domains** support  

## 🔧 Advanced Features

- **Auto-scaling**: Scale based on traffic
- **Preview environments**: Test PRs before merge
- **Rollbacks**: Easy rollback to previous versions
- **Monitoring**: Built-in metrics and alerts

## 💰 Pricing

Northflank offers competitive pricing:
- **CPU**: $0.01667 / vCPU / hour
- **Memory**: $0.00833 / GB / hour
- **Free tier** available to get started

## 🆘 Support

- Northflank documentation: Built-in help
- Community support: Available
- Enterprise support: For larger deployments

Your Flask app with Neon DB is now ready for production deployment on Northflank! 🚀
