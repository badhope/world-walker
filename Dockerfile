FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npx vite build

FROM python:3.11-slim
WORKDIR /workspace
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=frontend-builder /app/frontend/dist /workspace/frontend/dist
EXPOSE 8001
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8001"]