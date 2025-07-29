#!/bin/bash

# Kubernetes Deployment Script for Bot Marketplace
# Usage: ./k8s/scripts/deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
NAMESPACE="bot-marketplace"

echo "🚀 Deploying Bot Marketplace to Kubernetes ($ENVIRONMENT)"

# Function to check if kubectl is installed
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        echo "❌ kubectl is not installed. Please install kubectl first."
        exit 1
    fi
}

# Function to check cluster connection
check_cluster() {
    echo "🔍 Checking cluster connection..."
    if ! kubectl cluster-info &> /dev/null; then
        echo "❌ Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    echo "✅ Connected to cluster: $(kubectl config current-context)"
}

# Function to build and push images
build_images() {
    echo "📦 Building Docker images..."
    
    # Build API image
    docker build -t bot-marketplace-api:latest .
    
    # Build Celery worker image
    docker build -t bot-marketplace-celery:latest .
    
    # Build Celery beat image
    docker build -t bot-marketplace-beat:latest .
    
    echo "✅ Images built successfully"
}

# Function to deploy to Kubernetes
deploy_k8s() {
    echo "🌐 Deploying to Kubernetes..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply all resources
    kubectl apply -k k8s/
    
    echo "✅ Kubernetes resources deployed"
}

# Function to wait for deployment
wait_for_deployment() {
    echo "⏳ Waiting for deployments to be ready..."
    
    # Wait for MySQL
    kubectl wait --for=condition=available --timeout=300s deployment/mysql-deployment -n $NAMESPACE
    
    # Wait for Redis
    kubectl wait --for=condition=available --timeout=300s deployment/redis-deployment -n $NAMESPACE
    
    # Wait for API
    kubectl wait --for=condition=available --timeout=300s deployment/api-deployment -n $NAMESPACE
    
    # Wait for Celery worker
    kubectl wait --for=condition=available --timeout=300s deployment/celery-worker-deployment -n $NAMESPACE
    
    # Wait for Celery beat
    kubectl wait --for=condition=available --timeout=300s deployment/celery-beat-deployment -n $NAMESPACE
    
    echo "✅ All deployments are ready"
}

# Function to show deployment status
show_status() {
    echo "📊 Deployment Status:"
    echo "====================="
    
    # Show pods
    kubectl get pods -n $NAMESPACE
    
    echo ""
    echo "📈 Services:"
    kubectl get services -n $NAMESPACE
    
    echo ""
    echo "🌐 Ingress:"
    kubectl get ingress -n $NAMESPACE
    
    echo ""
    echo "📊 HPA:"
    kubectl get hpa -n $NAMESPACE
}

# Function to show logs
show_logs() {
    echo "📝 Recent logs from API:"
    kubectl logs -n $NAMESPACE deployment/api-deployment --tail=20
    
    echo ""
    echo "📝 Recent logs from Celery worker:"
    kubectl logs -n $NAMESPACE deployment/celery-worker-deployment --tail=20
}

# Main execution
main() {
    check_kubectl
    check_cluster
    
    case $ENVIRONMENT in
        "production")
            echo "🏭 Deploying to PRODUCTION"
            build_images
            deploy_k8s
            wait_for_deployment
            show_status
            ;;
        "staging")
            echo "🧪 Deploying to STAGING"
            # Modify for staging environment
            build_images
            deploy_k8s
            wait_for_deployment
            show_status
            ;;
        "development")
            echo "🔧 Deploying to DEVELOPMENT"
            # Modify for development environment
            build_images
            deploy_k8s
            wait_for_deployment
            show_status
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        *)
            echo "❌ Unknown environment: $ENVIRONMENT"
            echo "Usage: $0 [production|staging|development|status|logs]"
            exit 1
            ;;
    esac
}

main 