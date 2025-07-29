# 🚀 Kubernetes Deployment Guide - Bot Marketplace

## 📋 Overview

Bot Marketplace được thiết kế để chạy trên Kubernetes với các components:

- **API Service**: FastAPI web server (3 replicas)
- **Celery Worker**: Background task processing (2 replicas)
- **Celery Beat**: Task scheduler (1 replica)
- **MySQL**: Database (1 replica)
- **Redis**: Cache & message broker (1 replica)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Ingress       │    │   API Service   │    │   Celery Worker │
│   (nginx)       │───▶│   (3 replicas)  │───▶│   (2 replicas)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   MySQL         │    │   Redis         │
                       │   (1 replica)   │    │   (1 replica)   │
                       └─────────────────┘    └─────────────────┘
                                ▲                        ▲
                                │                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Celery Beat   │    │   Background    │
                       │   (1 replica)   │    │   Tasks         │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Install Docker
sudo apt-get update
sudo apt-get install docker.io
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
```

### 2. Build Images

```bash
# Build all images
docker build -t bot-marketplace-api:latest .
docker build -t bot-marketplace-celery:latest .
docker build -t bot-marketplace-beat:latest .
```

### 3. Deploy to Kubernetes

```bash
# Deploy to production
./k8s/scripts/deploy.sh production

# Deploy to staging
./k8s/scripts/deploy.sh staging

# Check status
./k8s/scripts/deploy.sh status

# View logs
./k8s/scripts/deploy.sh logs
```

## 📁 File Structure

```
k8s/
├── namespace.yaml              # Namespace definition
├── configmap.yaml              # Environment variables
├── secret.yaml                 # Sensitive data
├── mysql-deployment.yaml       # MySQL deployment & service
├── redis-deployment.yaml       # Redis deployment & service
├── api-deployment.yaml         # API deployment & ingress
├── celery-deployment.yaml      # Celery worker deployment
├── celery-beat-deployment.yaml # Celery beat deployment
├── hpa.yaml                    # Horizontal Pod Autoscaler
├── kustomization.yaml          # Kustomize configuration
└── scripts/
    └── deploy.sh               # Deployment script
```

## 🔧 Configuration

### Environment Variables

```yaml
# configmap.yaml
data:
  MYSQL_HOST: "mysql-service"
  REDIS_HOST: "redis-service"
  ENVIRONMENT: "production"
  SECRET_KEY: "your-secret-key"
```

### Secrets

```yaml
# secret.yaml
data:
  MYSQL_PASSWORD: Ym90cGFzc3dvcmQxMjM=  # base64 encoded
  DATABASE_URL: bXlzcWwrcHlteXNxbDovL2JvdHVzZXI6Ym90cGFzc3dvcmQxMjNAbXlzcWwtc2VydmljZTpzMzA2L2JvdF9tYXJrZXRwbGFjZQ==
```

## 📊 Monitoring

### Check Pod Status

```bash
kubectl get pods -n bot-marketplace
kubectl describe pod <pod-name> -n bot-marketplace
```

### Check Services

```bash
kubectl get services -n bot-marketplace
kubectl get ingress -n bot-marketplace
```

### Check HPA

```bash
kubectl get hpa -n bot-marketplace
kubectl describe hpa api-hpa -n bot-marketplace
```

### View Logs

```bash
# API logs
kubectl logs -n bot-marketplace deployment/api-deployment

# Celery worker logs
kubectl logs -n bot-marketplace deployment/celery-worker-deployment

# MySQL logs
kubectl logs -n bot-marketplace deployment/mysql-deployment
```

## 🔄 Scaling

### Manual Scaling

```bash
# Scale API to 5 replicas
kubectl scale deployment api-deployment --replicas=5 -n bot-marketplace

# Scale Celery worker to 3 replicas
kubectl scale deployment celery-worker-deployment --replicas=3 -n bot-marketplace
```

### Auto Scaling (HPA)

```bash
# Check HPA status
kubectl get hpa -n bot-marketplace

# Update HPA
kubectl edit hpa api-hpa -n bot-marketplace
```

## 🛠️ Troubleshooting

### Pod Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n bot-marketplace

# Check pod logs
kubectl logs <pod-name> -n bot-marketplace

# Check resource usage
kubectl top pods -n bot-marketplace
```

### Database Connection Issues

```bash
# Check MySQL service
kubectl get service mysql-service -n bot-marketplace

# Test connection from API pod
kubectl exec -it <api-pod-name> -n bot-marketplace -- mysql -h mysql-service -u botuser -p
```

### Redis Connection Issues

```bash
# Check Redis service
kubectl get service redis-service -n bot-marketplace

# Test connection from API pod
kubectl exec -it <api-pod-name> -n bot-marketplace -- redis-cli -h redis-service ping
```

## 🔒 Security

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
  namespace: bot-marketplace
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: mysql
    ports:
    - protocol: TCP
      port: 3306
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

### RBAC

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ServiceAccount
metadata:
  name: bot-marketplace-sa
  namespace: bot-marketplace
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: bot-marketplace-role
  namespace: bot-marketplace
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: bot-marketplace-rolebinding
  namespace: bot-marketplace
subjects:
- kind: ServiceAccount
  name: bot-marketplace-sa
  namespace: bot-marketplace
roleRef:
  kind: Role
  name: bot-marketplace-role
  apiGroup: rbac.authorization.k8s.io
```

## 📈 Performance

### Resource Limits

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### HPA Configuration

```yaml
spec:
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## 🚀 Production Checklist

- [ ] Update secrets with real values
- [ ] Configure ingress with SSL certificate
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure backup for MySQL
- [ ] Set up log aggregation
- [ ] Configure network policies
- [ ] Set up RBAC
- [ ] Configure resource limits
- [ ] Set up HPA
- [ ] Test disaster recovery 