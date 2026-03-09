version: "3.9"

services:
  # ---------- PostgreSQL ----------
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-techzone}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-techzone_secret}
      POSTGRES_DB: ${POSTGRES_DB:-techzone}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-techzone}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ---------- Redis ----------
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD:-redis_secret}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD:-redis_secret}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ---------- Elasticsearch ----------
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    restart: unless-stopped
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - es_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:9200/_cluster/health | grep -q '\"status\":\"green\"\\|\"status\":\"yellow\"'"]
      interval: 15s
      timeout: 10s
      retries: 10

  # ---------- Flask Backend ----------
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - FLASK_APP=run.py
      - FLASK_ENV=${FLASK_ENV:-production}
      - DATABASE_URL=postgresql://${POSTGRES_USER:-techzone}:${POSTGRES_PASSWORD:-techzone_secret}@db:5432/${POSTGRES_DB:-techzone}
      - REDIS_URL=redis://:${REDIS_PASSWORD:-redis_secret}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD:-redis_secret}@redis:6379/1
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD:-redis_secret}@redis:6379/2
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - SECRET_KEY=${SECRET_KEY:-change-me-in-production}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-jwt-change-me-in-production}
      - MAIL_SERVER=${MAIL_SERVER:-smtp.gmail.com}
      - MAIL_PORT=${MAIL_PORT:-587}
      - MAIL_USERNAME=${MAIL_USERNAME:-}
      - MAIL_PASSWORD=${MAIL_PASSWORD:-}
      - MAIL_DEFAULT_SENDER=${MAIL_DEFAULT_SENDER:-noreply@techzone.com}
    volumes:
      - ./backend:/app
    ports:
      - "5000:5000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      elasticsearch:
        condition: service_healthy
    command: gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"

  # ---------- Celery Worker ----------
  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - FLASK_APP=run.py
      - DATABASE_URL=postgresql://${POSTGRES_USER:-techzone}:${POSTGRES_PASSWORD:-techzone_secret}@db:5432/${POSTGRES_DB:-techzone}
      - REDIS_URL=redis://:${REDIS_PASSWORD:-redis_secret}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD:-redis_secret}@redis:6379/1
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD:-redis_secret}@redis:6379/2
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - SECRET_KEY=${SECRET_KEY:-change-me-in-production}
      - MAIL_SERVER=${MAIL_SERVER:-smtp.gmail.com}
      - MAIL_PORT=${MAIL_PORT:-587}
      - MAIL_USERNAME=${MAIL_USERNAME:-}
      - MAIL_PASSWORD=${MAIL_PASSWORD:-}
      - MAIL_DEFAULT_SENDER=${MAIL_DEFAULT_SENDER:-noreply@techzone.com}
    volumes:
      - ./backend:/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: celery -A celery_worker.celery worker --loglevel=info

  # ---------- Celery Beat (Scheduler) ----------
  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - FLASK_APP=run.py
      - DATABASE_URL=postgresql://${POSTGRES_USER:-techzone}:${POSTGRES_PASSWORD:-techzone_secret}@db:5432/${POSTGRES_DB:-techzone}
      - REDIS_URL=redis://:${REDIS_PASSWORD:-redis_secret}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD:-redis_secret}@redis:6379/1
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD:-redis_secret}@redis:6379/2
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - SECRET_KEY=${SECRET_KEY:-change-me-in-production}
    volumes:
      - ./backend:/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: celery -A celery_worker.celery beat --loglevel=info

  # ---------- React Frontend ----------
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: unless-stopped
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost/api
    depends_on:
      - backend

  # ---------- Nginx ----------
  nginx:
    image: nginx:1.25-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  redis_data:
  es_data:
