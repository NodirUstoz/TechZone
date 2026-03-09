# TechZone - Electronics E-Commerce Platform

A production-grade electronics e-commerce platform featuring product comparison, a comprehensive specifications database, expert tech reviews, intelligent price alerts, and warranty management.

## Project Goal

TechZone aims to be the definitive online destination for purchasing electronics, providing buyers with the tools they need to make informed decisions. By combining detailed product specifications, side-by-side comparisons, professional reviews, historical price tracking, and post-purchase warranty management, TechZone delivers an end-to-end electronics shopping experience that goes far beyond a simple storefront.

## Key Features

### Product Management
- Full CRUD operations for electronics products with rich metadata
- Hierarchical category system (e.g., Laptops > Gaming Laptops)
- Multi-image support with primary image selection
- Brand management with logo and description
- Detailed specification tables per product (CPU, RAM, storage, display, etc.)

### Product Comparison
- Side-by-side comparison of up to 4 products
- Auto-aligned specification rows for easy visual scanning
- Save and share comparison lists
- Highlight specification differences across compared products

### Specifications Database
- Structured specification schema per category
- Filterable and searchable specifications
- Specification-based product recommendations
- Category-specific specification templates

### Tech Reviews
- Professional editorial reviews with detailed scoring (performance, value, design, etc.)
- User reviews with verified purchase badges
- Pros/cons lists and final verdict summaries
- Review helpfulness voting

### Price Alerts
- Set target price notifications per product
- Full price history tracking with date-stamped entries
- Price trend visualization (line charts)
- Email and in-app notifications when prices drop

### Warranty Management
- Register product warranties post-purchase
- Track warranty expiration dates
- Warranty claim submission and status tracking
- Automated expiry reminders via email

### Order Management
- Shopping cart with persistent state
- Multi-step checkout flow
- Order history with status tracking
- Payment processing integration
- Invoice generation

### Search and Discovery
- Full-text search powered by Elasticsearch
- Faceted filtering (brand, price range, specs)
- Category browsing with breadcrumbs
- Featured and trending product sections

## Architecture

```
                    +------------------+
                    |   Nginx Reverse  |
                    |      Proxy       |
                    +--------+---------+
                             |
              +--------------+--------------+
              |                             |
     +--------v--------+         +---------v--------+
     |  React Frontend |         |  Flask Backend    |
     |  (Port 3000)    |         |  (Port 5000)      |
     +-----------------+         +---+----+----+-----+
                                     |    |    |
                          +----------+    |    +----------+
                          |               |               |
                 +--------v---+    +------v-----+   +-----v-------+
                 | PostgreSQL |    |    Redis    |   | Elasticsearch|
                 | (Port 5432)|    | (Port 6379)|   | (Port 9200)  |
                 +------------+    +------+-----+   +--------------+
                                         |
                                  +------v-----+
                                  |   Celery    |
                                  |   Workers   |
                                  +-------------+
```

### Data Flow

1. **Client requests** hit Nginx, which routes to either the React SPA or the Flask API.
2. **Flask API** handles business logic, reads/writes PostgreSQL, caches hot data in Redis.
3. **Elasticsearch** powers full-text product search and faceted filtering.
4. **Celery workers** consume tasks from Redis (broker) for background jobs: price checking, email dispatch, warranty reminders.
5. **React frontend** communicates with the API via Axios, manages state with Redux Toolkit.

## Tech Stack

| Layer          | Technology                        |
|----------------|-----------------------------------|
| Backend        | Python 3.11, Flask, Flask-RESTful |
| Frontend       | React 18, Redux Toolkit, React Router |
| Database       | PostgreSQL 15                     |
| Cache / Broker | Redis 7                           |
| Search         | Elasticsearch 8                   |
| Task Queue     | Celery 5                          |
| Reverse Proxy  | Nginx                             |
| Containerization | Docker, Docker Compose          |
| ORM            | SQLAlchemy + Alembic              |
| Serialization  | Marshmallow                       |
| Auth           | JWT (Flask-JWT-Extended)          |
| Charts         | Recharts                          |

## Folder Structure

```
techzone/
|-- docker-compose.yml
|-- .env.example
|-- .gitignore
|-- README.md
|-- nginx/
|   +-- nginx.conf
|-- backend/
|   |-- requirements.txt
|   |-- run.py
|   |-- celery_worker.py
|   |-- migrations/
|   |   +-- env.py
|   +-- app/
|       |-- __init__.py
|       |-- config.py
|       |-- extensions.py
|       |-- models/
|       |   |-- __init__.py
|       |   |-- user.py
|       |   |-- product.py
|       |   |-- order.py
|       |   |-- review.py
|       |   |-- comparison.py
|       |   |-- price_alert.py
|       |   +-- warranty.py
|       |-- api/
|       |   |-- __init__.py
|       |   |-- auth.py
|       |   |-- products.py
|       |   |-- orders.py
|       |   |-- reviews.py
|       |   |-- comparisons.py
|       |   |-- price_alerts.py
|       |   |-- warranties.py
|       |   +-- admin.py
|       |-- services/
|       |   |-- __init__.py
|       |   |-- auth_service.py
|       |   |-- product_service.py
|       |   |-- order_service.py
|       |   |-- notification_service.py
|       |   +-- price_tracker.py
|       |-- tasks/
|       |   |-- __init__.py
|       |   |-- price_tasks.py
|       |   |-- notification_tasks.py
|       |   +-- email_tasks.py
|       |-- utils/
|       |   |-- __init__.py
|       |   |-- decorators.py
|       |   |-- pagination.py
|       |   +-- validators.py
|       +-- schemas/
|           |-- __init__.py
|           |-- user_schema.py
|           |-- product_schema.py
|           +-- order_schema.py
+-- frontend/
    |-- package.json
    |-- public/
    |   +-- index.html
    +-- src/
        |-- index.js
        |-- App.jsx
        |-- api/
        |   |-- client.js
        |   |-- products.js
        |   |-- auth.js
        |   +-- orders.js
        |-- components/
        |   |-- layout/
        |   |   |-- Navbar.jsx
        |   |   +-- Footer.jsx
        |   |-- products/
        |   |   |-- ProductCard.jsx
        |   |   |-- ProductGrid.jsx
        |   |   |-- SpecTable.jsx
        |   |   +-- PriceChart.jsx
        |   |-- comparison/
        |   |   +-- ComparisonView.jsx
        |   |-- reviews/
        |   |   +-- TechReview.jsx
        |   +-- auth/
        |       |-- LoginForm.jsx
        |       +-- RegisterForm.jsx
        |-- pages/
        |   |-- HomePage.jsx
        |   |-- ProductPage.jsx
        |   |-- CategoryPage.jsx
        |   |-- ComparisonPage.jsx
        |   |-- CartPage.jsx
        |   |-- ProfilePage.jsx
        |   +-- AdminDashboard.jsx
        |-- store/
        |   |-- store.js
        |   |-- authSlice.js
        |   +-- cartSlice.js
        |-- hooks/
        |   +-- useAuth.js
        +-- styles/
            +-- global.css
```

## Setup and Installation

### Prerequisites

- Docker and Docker Compose installed
- Git

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/techzone.git
   cd techzone
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration values
   ```

3. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```

4. **Run database migrations (first run):**
   ```bash
   docker-compose exec backend flask db upgrade
   ```

5. **Seed the database with initial data (optional):**
   ```bash
   docker-compose exec backend flask seed
   ```

6. **Access the application:**
   - Frontend: http://localhost
   - API: http://localhost/api
   - Elasticsearch: http://localhost:9200

### Local Development (without Docker)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
pip install -r requirements.txt
flask db upgrade
python run.py
```

#### Frontend

```bash
cd frontend
npm install
npm start
```

#### Celery Worker

```bash
cd backend
celery -A celery_worker.celery worker --loglevel=info
```

## API Documentation

### Authentication

| Method | Endpoint             | Description             | Auth  |
|--------|----------------------|-------------------------|-------|
| POST   | /api/auth/register   | Register new user       | No    |
| POST   | /api/auth/login      | Login, receive JWT      | No    |
| POST   | /api/auth/refresh    | Refresh access token    | JWT   |
| GET    | /api/auth/me         | Get current user        | JWT   |
| PUT    | /api/auth/me         | Update profile          | JWT   |

### Products

| Method | Endpoint                     | Description                   | Auth    |
|--------|------------------------------|-------------------------------|---------|
| GET    | /api/products                | List products (paginated)     | No      |
| GET    | /api/products/:id            | Get product details           | No      |
| POST   | /api/products                | Create product                | Admin   |
| PUT    | /api/products/:id            | Update product                | Admin   |
| DELETE | /api/products/:id            | Delete product                | Admin   |
| GET    | /api/products/search         | Full-text search              | No      |
| GET    | /api/products/:id/specs      | Get product specifications    | No      |
| GET    | /api/categories              | List all categories           | No      |
| GET    | /api/categories/:id/products | Products by category          | No      |

### Orders

| Method | Endpoint               | Description              | Auth  |
|--------|------------------------|--------------------------|-------|
| POST   | /api/orders            | Create order             | JWT   |
| GET    | /api/orders            | List user orders         | JWT   |
| GET    | /api/orders/:id        | Get order details        | JWT   |
| PUT    | /api/orders/:id/cancel | Cancel order             | JWT   |

### Reviews

| Method | Endpoint                         | Description               | Auth  |
|--------|----------------------------------|---------------------------|-------|
| GET    | /api/products/:id/reviews        | Get product reviews       | No    |
| POST   | /api/products/:id/reviews        | Submit review             | JWT   |
| PUT    | /api/reviews/:id                 | Update review             | JWT   |
| DELETE | /api/reviews/:id                 | Delete review             | JWT   |
| GET    | /api/products/:id/tech-review    | Get tech/editorial review | No    |
| POST   | /api/products/:id/tech-review    | Create tech review        | Admin |

### Comparisons

| Method | Endpoint                       | Description              | Auth  |
|--------|--------------------------------|--------------------------|-------|
| POST   | /api/comparisons               | Create comparison list   | JWT   |
| GET    | /api/comparisons               | Get user comparisons     | JWT   |
| GET    | /api/comparisons/:id           | Get comparison details   | No    |
| PUT    | /api/comparisons/:id/products  | Add/remove products      | JWT   |

### Price Alerts

| Method | Endpoint                        | Description              | Auth  |
|--------|---------------------------------|--------------------------|-------|
| POST   | /api/price-alerts               | Create price alert       | JWT   |
| GET    | /api/price-alerts               | List user alerts         | JWT   |
| DELETE | /api/price-alerts/:id           | Delete alert             | JWT   |
| GET    | /api/products/:id/price-history | Get price history        | No    |

### Warranties

| Method | Endpoint                    | Description              | Auth  |
|--------|-----------------------------|--------------------------|-------|
| POST   | /api/warranties             | Register warranty        | JWT   |
| GET    | /api/warranties             | List user warranties     | JWT   |
| GET    | /api/warranties/:id         | Get warranty details     | JWT   |
| POST   | /api/warranties/:id/claim   | Submit warranty claim    | JWT   |

### Admin

| Method | Endpoint                   | Description              | Auth  |
|--------|----------------------------|--------------------------|-------|
| GET    | /api/admin/dashboard       | Dashboard statistics     | Admin |
| GET    | /api/admin/users           | List all users           | Admin |
| PUT    | /api/admin/users/:id       | Update user role/status  | Admin |
| GET    | /api/admin/orders          | List all orders          | Admin |
| PUT    | /api/admin/orders/:id      | Update order status      | Admin |

## User Roles

| Role     | Permissions                                                                 |
|----------|-----------------------------------------------------------------------------|
| Guest    | Browse products, search, view reviews, view comparisons                     |
| Customer | All guest permissions + place orders, write reviews, create price alerts, manage warranties, save comparisons |
| Admin    | All customer permissions + manage products/categories/brands, write tech reviews, manage orders, view dashboard, manage users |

## Business Logic

### Price Alert Engine
- Celery beat schedules price checks every 6 hours.
- When a product's current price is less than or equal to a user's target price, an email notification is dispatched and the alert is marked as triggered.
- Price history records are created each time a product price is updated, enabling trend charts.

### Order Lifecycle
1. **Pending** - Order created, awaiting payment.
2. **Paid** - Payment confirmed.
3. **Processing** - Order being prepared.
4. **Shipped** - Order dispatched, tracking number assigned.
5. **Delivered** - Order received by customer.
6. **Cancelled** - Order cancelled (only from Pending or Paid status).

### Review Scoring
- User reviews: 1-5 star rating with optional text.
- Tech reviews: Multi-dimensional scoring (performance, value, design, features, battery) averaged into a final score out of 10.
- Products display both aggregate user rating and editorial score.

### Warranty Flow
1. Customer registers a warranty by providing order item and serial number.
2. System validates purchase and sets expiry based on product warranty duration.
3. Customer can submit claims against active warranties.
4. Admins review and resolve warranty claims.
5. Automated email reminders are sent 30 days before warranty expiry.

## Roadmap

- [ ] Wishlist functionality
- [ ] Product Q&A section
- [ ] Loyalty points and rewards program
- [ ] Multi-currency and internationalization
- [ ] AI-powered product recommendations
- [ ] Augmented reality product preview
- [ ] Seller marketplace (multi-vendor support)
- [ ] Mobile application (React Native)
- [ ] Real-time chat support integration
- [ ] Advanced analytics dashboard with sales forecasting

## License

This project is proprietary software. All rights reserved.
