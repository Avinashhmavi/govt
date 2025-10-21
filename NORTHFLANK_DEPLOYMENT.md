# Northflank Deployment Configuration

## Project Setup
- **Project Name**: govt-directory
- **Service Type**: Web Application
- **Runtime**: Docker Container

## Environment Variables
Set these in Northflank dashboard:

```bash
# Database Configuration (Neon DB)
DB_HOST=ep-steep-band-adymw02q-pooler.c-2.us-east-1.aws.neon.tech
DB_PORT=5432
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=npg_zJ5YA8akldbi
DB_SSLMODE=require
DB_CHANNEL_BINDING=require

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secure-secret-key-here
PORT=5000

# OpenAI API Key (if using voice features)
OPENAI_API_KEY=your_openai_api_key_here
```

## Deployment Steps

### 1. Connect GitHub Repository
- Go to Northflank dashboard
- Click "New Project"
- Connect your GitHub repository: `Avinashhmavi/govt`
- Select branch: `neodb`

### 2. Configure Service
- **Service Name**: govt-directory
- **Build Context**: Root directory
- **Dockerfile**: Use the provided Dockerfile
- **Port**: 5000

### 3. Set Environment Variables
Copy the environment variables above into Northflank's environment section.

### 4. Configure Resources
- **CPU**: 0.5 vCPU (minimum)
- **Memory**: 1GB RAM
- **Storage**: 2GB (for static files)

### 5. Configure Domain
- Enable custom domain or use Northflank's provided domain
- Set up SSL certificate

## Build Configuration
The Dockerfile will:
- Use Python 3.11 slim image
- Install all dependencies from requirements.txt
- Copy application code
- Run with Gunicorn for production
- Include health checks

## Static Files
Static files (images, CSS) are included in the Docker image and served by Flask.

## Database
The application connects to your existing Neon PostgreSQL database.

## Monitoring
Northflank provides built-in:
- Application logs
- Performance metrics
- Health checks
- Automatic restarts

## Scaling
You can easily scale the application:
- Horizontal scaling (more instances)
- Vertical scaling (more CPU/memory)
- Auto-scaling based on traffic

## Backup & Recovery
- Application code is in Git
- Database backups handled by Neon
- Static files included in Docker image

## Security
- Non-root user in container
- Environment variables for secrets
- SSL/TLS termination
- Health checks for monitoring
