# Manual Northflank Deployment (Without GitHub Integration)

## Option 1: Upload Docker Image to Docker Hub

### 1. Build Docker Image Locally
```bash
# Build the image
docker build -t avinashhmavi/govt-directory:latest .

# Push to Docker Hub
docker push avinashhmavi/govt-directory:latest
```

### 2. Deploy from Docker Hub in Northflank
- In Northflank, choose "Deploy from Docker Hub"
- Image: `avinashhmavi/govt-directory:latest`
- Set environment variables as before

## Option 2: Upload Source Code Directly

### 1. Create Deployment Package
```bash
# Create a zip file of your source code
zip -r govt-deployment.zip . -x "*.git*" "*.DS_Store*" "__pycache__/*"
```

### 2. Upload to Northflank
- In Northflank, choose "Upload Source"
- Upload the zip file
- Set build context and Dockerfile

## Option 3: Use Git Clone in Northflank

### 1. Use Public Repository URL
- In Northflank, choose "Deploy from Git"
- Repository URL: `https://github.com/Avinashhmavi/govt.git`
- Branch: `neodb`
- This should work even without the GitHub app
