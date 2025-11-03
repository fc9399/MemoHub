# Deployment Guide (Frontend, Backend, and EKS)

This deployment note is for reference only.

This guide covers local containerization, common cloud hosting (Vercel/Render/EC2), and production deployment on AWS EKS. Use the root `env.example` to create your `.env` with required variables.

---

## 1. Prerequisites
- Installed: Docker, docker-compose, Node.js 18+, Python 3.10+
- Cloud options (choose as needed):
  - Vercel (Frontend) / Render or EC2 (Backend)
  - or AWS stack: ECR, EKS, ALB Ingress Controller, ACM certificate, Route53 DNS
- Environment variables: copy `env.example` to `.env` and fill in values (Backend requires AWS and OpenAI/NIM configs, etc.).

---

## 2. Directory Layout
- Backend (FastAPI): repo root (`main.py`, `routers/`, `services/`, etc.)
- Frontend (Next.js): `UI/memohub`

---

## 3. Local Containers (one command)

### 3.1 Reference Dockerfiles (suggested)
- Backend `Dockerfile.backend` (FastAPI + uvicorn)
- Frontend `Dockerfile.frontend` (Next.js standalone)

Place them at the repo root and reference in `docker-compose.yml`. You can use the compose below directly.

### 3.2 docker-compose (example)
```yaml
version: "3.9"
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    env_file: .env
    ports:
      - "8000:8000"
    restart: unless-stopped

  frontend:
    build:
      context: ./UI/memohub
      dockerfile: Dockerfile.frontend
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    ports:
      - "3001:3000"
    depends_on:
      - backend
    restart: unless-stopped
```
Run:
```bash
docker compose up -d --build
```

---

## 4. Frontend Deployment

### 4.1 Vercel (recommended)
- Project root: `UI/memohub`
- Build Command: `npm run build`
- Output: Next.js default (Node `next start` or Vercel serverless)
- Env vars:
  - `NEXT_PUBLIC_API_URL` pointing to the backend (e.g. `https://api.example.com`)

### 4.2 Self-hosted (Docker/EC2)
- Build and run with `Dockerfile.frontend`:
```bash
cd UI/memohub
docker build -t memohub-frontend -f Dockerfile.frontend .
docker run -p 3000:3000 memohub-frontend
```
- Put behind Nginx or another reverse proxy (TLS/HTTP2/caching).

---

## 5. Backend Deployment

### 5.1 Render / EC2 (Docker)
- Build and run:
```bash
docker build -t memohub-backend -f Dockerfile.backend .
docker run --env-file .env -p 8000:8000 memohub-backend
```
- Expose 8000 or put behind Nginx with TLS.

### 5.2 Process supervisor (non-container)
- `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2`
- Use systemd/supervisor + Nginx.

---

## 6. AWS EKS (production path)

### 6.1 Build and push images to ECR
```bash
# Login to ECR
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com

# Build images
docker build -t memohub-backend:prod -f Dockerfile.backend .
docker build -t memohub-frontend:prod -f UI/memohub/Dockerfile.frontend UI/memohub

# Tag and push
docker tag memohub-backend:prod <account>.dkr.ecr.<region>.amazonaws.com/memohub-backend:prod
docker tag memohub-frontend:prod <account>.dkr.ecr.<region>.amazonaws.com/memohub-frontend:prod

docker push <account>.dkr.ecr.<region>.amazonaws.com/memohub-backend:prod
docker push <account>.dkr.ecr.<region>.amazonaws.com/memohub-frontend:prod
```

### 6.2 Kubernetes manifests (minimal example)
- Namespace: `memohub`
- Secret: store backend `.env` keys and frontend `NEXT_PUBLIC_API_BASE`

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: memohub
---
apiVersion: v1
kind: Secret
metadata:
  name: backend-env
  namespace: memohub
stringData:
  # fill required keys from env.example (example)
  AWS_REGION: us-east-1
  S3_BUCKET_NAME: memohub-files
  OPENAI_API_KEY: <redacted>
  # ... others
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: memohub
spec:
  replicas: 2
  selector:
    matchLabels: { app: backend }
  template:
    metadata:
      labels: { app: backend }
    spec:
      containers:
        - name: backend
          image: <account>.dkr.ecr.<region>.amazonaws.com/memohub-backend:prod
          ports:
            - containerPort: 8000
          envFrom:
            - secretRef: { name: backend-env }
          resources:
            requests: { cpu: "250m", memory: "512Mi" }
            limits: { cpu: "1", memory: "1Gi" }
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: memohub
spec:
  selector: { app: backend }
  ports:
    - name: http
      port: 80
      targetPort: 8000
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: memohub
spec:
  replicas: 2
  selector:
    matchLabels: { app: frontend }
  template:
    metadata:
      labels: { app: frontend }
    spec:
      containers:
        - name: frontend
          image: <account>.dkr.ecr.<region>.amazonaws.com/memohub-frontend:prod
          ports:
            - containerPort: 3000
          env:
            - name: NEXT_PUBLIC_API_URL
              value: "https://api.example.com" # backend ingress hostname
          resources:
            requests: { cpu: "250m", memory: "512Mi" }
            limits: { cpu: "1", memory: "1Gi" }
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: memohub
spec:
  selector: { app: frontend }
  ports:
    - name: http
      port: 80
      targetPort: 3000
```

### 6.3 Ingress and DNS
- Install AWS Load Balancer Controller.
- Request an ACM certificate (in the same region as ALB, e.g. us-east-1).
- Configure two Ingresses: `api.example.com` -> `Service/backend`, `app.example.com` -> `Service/frontend`.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: backend-ingress
  namespace: memohub
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP":80,"HTTPS":443}]'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:...:certificate/...
spec:
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: backend
                port:
                  number: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: frontend-ingress
  namespace: memohub
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP":80,"HTTPS":443}]'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:...:certificate/...
spec:
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 80
```

Finally, point Route53 CNAME records to the ALB DNS for `api.example.com` and `app.example.com`.

---

## 7. Suggested Files to Add
- `Dockerfile.backend`, `Dockerfile.frontend`
- `docker-compose.yml`
- `k8s/namespace.yaml`, `k8s/backend.yaml`, `k8s/frontend.yaml`, `k8s/ingress.yaml`
- `infra/README.md` (AWS resources, permissions, and runbook)


