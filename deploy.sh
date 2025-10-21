#!/bin/bash
# Docker Hub Deployment Script

echo "🐳 Building Docker image for Northflank deployment..."

# Build the Docker image
docker build -t avinashhmavi/govt-directory:latest .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    
    # Ask user if they want to push to Docker Hub
    read -p "Do you want to push to Docker Hub? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📤 Pushing to Docker Hub..."
        docker push avinashhmavi/govt-directory:latest
        
        if [ $? -eq 0 ]; then
            echo "✅ Image pushed to Docker Hub successfully!"
            echo ""
            echo "🚀 Now you can deploy on Northflank:"
            echo "1. Go to Northflank dashboard"
            echo "2. Create new project"
            echo "3. Choose 'Deploy from Docker Hub'"
            echo "4. Use image: avinashhmavi/govt-directory:latest"
            echo "5. Set environment variables"
            echo "6. Deploy!"
        else
            echo "❌ Failed to push to Docker Hub"
        fi
    else
        echo "ℹ️  Image built locally. You can push manually with:"
        echo "   docker push avinashhmavi/govt-directory:latest"
    fi
else
    echo "❌ Failed to build Docker image"
    exit 1
fi
