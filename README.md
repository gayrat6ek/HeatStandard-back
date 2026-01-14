# iiko Integration Backend

FastAPI backend application with Docker, PostgreSQL, and iiko Cloud API integration for managing products, organizations, restaurant sections, and orders.

## Features

- 🚀 **FastAPI** - Modern, fast web framework for building APIs
- 🐘 **PostgreSQL** - Robust relational database
- 🐳 **Docker** - Containerized deployment
- 🔄 **iiko Cloud API Integration** - Sync organizations, products, sections, and create orders
- 📝 **Alembic** - Database migrations
- 🎯 **RESTful API** - Clean, versioned API endpoints
- 📊 **Automatic API Documentation** - Swagger UI and ReDoc

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── organizations.py
│   │       ├── products.py
│   │       ├── terminal_groups.py
│   │       ├── sections.py
│   │       └── orders.py
│   ├── crud/
│   │   ├── organization.py
│   │   ├── product.py
│   │   ├── terminal_group.py
│   │   ├── section.py
│   │   └── order.py
│   ├── models/
│   │   ├── organization.py
│   │   ├── product.py
│   │   ├── terminal_group.py
│   │   ├── section.py
│   │   ├── order.py
│   │   └── order_item.py
│   ├── schemas/
│   │   ├── organization.py
│   │   ├── product.py
│   │   ├── terminal_group.py
│   │   ├── section.py
│   │   ├── order.py
│   │   └── order_item.py
│   ├── services/
│   │   └── iiko_service.py
│   ├── utils/
│   │   ├── logger.py
│   │   └── exceptions.py
│   ├── scripts/
│   │   └── test_iiko.py
│   ├── config.py
│   ├── database.py
│   └── main.py
├── alembic/
│   ├── versions/
│   └── env.py
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
├── .env.example
└── README.md
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Make (optional, but recommended)

### Installation

1. **Clone the repository** (if applicable)

2. **Initialize the project:**
   ```bash
   make init
   ```
   This will:
   - Create `.env` file from `.env.example`
   - Build Docker images
   - Start services
   - Run database migrations

3. **Or do it manually:**
   ```bash
   # Copy environment file
   cp .env.example .env
   
   # Update .env with your settings (especially IIKO_TRANSPORT_KEY)
   
   # Build and start services
   make build
   make up
   
   # Run migrations
   make migrate
   ```

## Usage

### API Documentation

Once the application is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Common Commands

```bash
# Start services
make up

# Stop services
make down

# View logs
make logs

# Access app container shell
make shell

# Access PostgreSQL shell
make db-shell

# Run database migrations
make migrate

# Create new migration
make makemigrations

# Run tests
make test

# Format code
make format

# Run linters
make lint

# Clean up (remove containers and volumes)
make clean
```

### API Endpoints

#### Organizations

- `GET /api/v1/organizations` - List all organizations
- `GET /api/v1/organizations/{id}` - Get organization by ID
- `POST /api/v1/organizations/sync` - Sync organizations from iiko

#### Products

- `GET /api/v1/products` - List all products (with filters)
- `GET /api/v1/products/{id}` - Get product by ID
- `POST /api/v1/products/sync` - Sync products from iiko

#### Sections

- `GET /api/v1/sections` - List all restaurant sections
- `GET /api/v1/sections/{id}` - Get section by ID
- `POST /api/v1/sections/sync` - Sync sections from iiko

#### Orders

- `GET /api/v1/orders` - List all orders
- `GET /api/v1/orders/{id}` - Get order by ID
- `POST /api/v1/orders` - Create order and send to iiko

### Workflow Example

1. **Sync organizations from iiko:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/organizations/sync
   ```

2. **Sync products:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/products/sync
   ```

3. **Sync restaurant sections:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/sections/sync
   ```

4. **Create an order:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/orders \
     -H "Content-Type: application/json" \
     -d '{
       "organization_id": "uuid-here",
       "customer_name": "John Doe",
       "customer_phone": "+1234567890",
       "items": [
         {
           "product_id": "uuid-here",
           "product_name": "Product Name",
           "quantity": 2,
           "price": 10.00,
           "total": 20.00
         }
       ]
     }'
   ```

## Configuration

All configuration is managed through environment variables in the `.env` file:

- `DATABASE_URL` - PostgreSQL connection string
- `IIKO_API_BASE_URL` - iiko API base URL (default: https://api-ru.iiko.services)
- `IIKO_TRANSPORT_KEY` - Your iiko transport API key
- `CORS_ORIGINS` - Allowed CORS origins
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## Development

### Adding New Endpoints

1. Create new router in `app/api/v1/`
2. Add CRUD operations in `app/crud/`
3. Define schemas in `app/schemas/`
4. Create models in `app/models/`
5. Register router in `app/api/v1/__init__.py`

### Database Migrations

```bash
# Create a new migration
make makemigrations

# Apply migrations
make migrate
```

## Production Deployment

For production deployment:

1. Update `.env` with production values
2. Set `DEBUG=False`
3. Use a production-grade PostgreSQL instance
4. Configure proper CORS origins
5. Set up SSL/TLS certificates
6. Use a reverse proxy (nginx, traefik)
7. Set up monitoring and logging

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### iiko API Issues

Check the logs for detailed error messages:
```bash
make logs
```

Common issues:
- Invalid transport key
- Network connectivity
- Rate limiting (max 5 organizations per nomenclature request)

## License

[Your License Here]

## Support

For issues and questions, please contact [your contact information].
