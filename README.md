# FastAPI Data Taxi API

A production-ready REST API built with FastAPI that serves historical NYC taxi trip data. The API retrieves data from NYC Taxi and Limousine Commission parquet files and makes it accessible through a RESTful interface.

## Project Overview

This project provides a REST API endpoint to query historical taxi trip data from New York City. The data is stored in monthly parquet files and is automatically downloaded and cached when needed. The API supports pagination and filtering by timestamp.

## Features

- RESTful API built with FastAPI
- Automatic download and caching of NYC taxi trip data parquet files
- Query trips by timestamp with configurable result limits
- Health check endpoint for monitoring
- Request timing middleware with Elasticsearch integration
- Docker support with multiple build strategies
- Comprehensive testing suite
- Production-ready deployment configuration

## API Endpoints

### GET /health

Health check endpoint that returns the API status.

**Response:**
```json
{
  "status": "Healthy!!!"
}
```

### GET /trips

Retrieves taxi trips starting from a specified timestamp.

**Query Parameters:**
- `from_ms` (required): Unix timestamp in milliseconds to start the search from
- `n_results` (optional): Maximum number of results to return (default: 100)

**Response:**
```json
{
  "trips": [
    {
      "tpep_pickup_datetime": "2023-01-24T10:30:00",
      "tpep_dropoff_datetime": "2023-01-24T10:45:00",
      "trip_distance": 2.5,
      "fare_amount": 12.50
    }
  ],
  "next_from_ms": 1674561817000,
  "message": "Success. Returned 100 trips."
}
```

## Project Structure

```
.
├── src/
│   ├── api.py              # FastAPI application and route handlers
│   ├── backend.py          # Core business logic for trip data retrieval
│   ├── config.py           # Configuration settings
│   ├── middleware.py       # Request timing and Elasticsearch logging middleware
│   └── utils.py            # Utility functions
├── tests/
│   └── test_read_parquet.py  # Unit tests
├── docker-compose.yml      # Elasticsearch and Kibana services
├── Dockerfile.naive        # Basic Docker build
├── Dockerfile.1stage       # Single-stage Docker build
├── Dockerfile.2stage       # Multi-stage Docker build
├── Makefile                # Build and deployment commands
├── pyproject.toml          # Poetry dependencies and configuration
└── README.md               # This file
```

## Prerequisites

- Python 3.10 or higher
- Poetry (Python dependency management)
- Docker and Docker Compose (for containerized deployment)
- Make (for using Makefile commands)

## Installation

1. Clone this repository and navigate to the project root directory.

2. Install Python Poetry if you haven't already. Poetry is used for dependency management and virtual environment creation.

3. Install project dependencies and create a virtual environment:
   ```
   make install
   ```

   This command will:
   - Download and install Poetry
   - Create a Python 3.10 virtual environment
   - Install all project dependencies

## Running the API Locally

### Development Mode

Run the API in development mode with auto-reload:
```
make run-dev
```

The API will be available at `http://localhost:8095` (or the port specified in the Makefile).

### Docker Mode

Build and run the API using Docker:
```
make all
```

This command will:
- Run linting and formatting checks
- Execute tests
- Build the Docker image (multi-stage build)
- Run the containerized API

### Health Check

Verify the API is running:
```
make health-check-local
```

### Sample Request

Test the API with a sample request:
```
make sample-request-local
```

## Configuration

### Environment Variables

- `CACHE_DIR`: Directory path for caching parquet files (default: `/tmp/taxi-data-api-python/`)
- `ELASTICSEARCH_HOST`: Elasticsearch host URL (default: `http://localhost:9200`)
- `ELASTICSEARCH_INDEX`: Elasticsearch index name (default: `taxi_data_api`)
- `PORT`: Port number for the API server (default: `8095`)

## Monitoring with Elasticsearch and Kibana

The API includes middleware that logs request timing data to Elasticsearch. To set up monitoring:

1. Start Elasticsearch and Kibana services:
   ```
   make start-infra
   ```

2. Access Kibana dashboard at `http://localhost:5601`

3. The middleware automatically logs:
   - Endpoint path
   - HTTP method
   - Process time (response time)
   - Timestamp

4. Stop the infrastructure services:
   ```
   make stop-infra
   ```

## Testing

Run the test suite:
```
make test
```

The tests verify that parquet files can be read correctly and return valid data.

## Code Quality

### Linting

Check and fix code style issues:
```
make lint
```

### Formatting

Format code according to project standards:
```
make format
```

## Docker Build Strategies

The project includes three Docker build strategies:

1. **Naive Build** (`Dockerfile.naive`): Basic Docker build without optimization
2. **Single-Stage Build** (`Dockerfile.1stage`): Optimized single-stage build
3. **Multi-Stage Build** (`Dockerfile.2stage`): Production-ready multi-stage build (default)

Compare image sizes:
```
make check-image-sizes
```

## Data Source

The API retrieves data from the NYC Taxi and Limousine Commission (TLC) Trip Record Data. The data is stored in monthly parquet files and is automatically downloaded from the official TLC data repository when needed.

The parquet files are cached locally to improve performance on subsequent requests for the same month's data.

## Dependencies

### Core Dependencies
- FastAPI: Modern web framework for building APIs
- Uvicorn: ASGI server for running FastAPI
- Pandas: Data manipulation and analysis
- PyArrow: Parquet file reading support
- Requests: HTTP library for downloading data files
- Loguru: Advanced logging library
- Elasticsearch: Search and analytics engine for monitoring

### Development Dependencies
- Pytest: Testing framework
- Ruff: Fast Python linter and formatter

## Makefile Commands

- `make install`: Install Poetry and project dependencies
- `make run-dev`: Run API in development mode
- `make build`: Build Docker image (multi-stage)
- `make run`: Build and run Docker container
- `make test`: Run test suite
- `make lint`: Check and fix code style
- `make format`: Format code
- `make all`: Run lint, format, test, build, and run
- `make health-check-local`: Check API health
- `make sample-request-local`: Send sample API request
- `make start-infra`: Start Elasticsearch and Kibana
- `make stop-infra`: Stop Elasticsearch and Kibana

## License

This project is provided as-is for educational and demonstration purposes.
