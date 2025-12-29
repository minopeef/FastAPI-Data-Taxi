from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field

from src.backend import Trip, get_trips
from src.middleware import TimingMiddleware

app = FastAPI(
    title='NYC Taxi Data API',
    description='REST API for querying historical NYC taxi trip data',
    version='1.0.0',
)

app.add_middleware(TimingMiddleware)

# Configuration constants
MIN_TIMESTAMP_MS = 946684800000  # 2000-01-01
MAX_TIMESTAMP_MS = 4102444800000  # 2100-01-01
MIN_RESULTS = 1
MAX_RESULTS = 10000
DEFAULT_RESULTS = 100


class TripsResponse(BaseModel):
    trips: Optional[list[Trip]] = None
    next_from_ms: Optional[int] = None
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


@app.get(
    '/trips',
    response_model=TripsResponse,
    responses={
        400: {'model': ErrorResponse, 'description': 'Invalid request parameters'},
        500: {'model': ErrorResponse, 'description': 'Internal server error'},
    },
)
def get_trip(
    from_ms: int = Query(
        ...,
        description='Unix timestamp in milliseconds to start the search from',
        ge=MIN_TIMESTAMP_MS,
        le=MAX_TIMESTAMP_MS,
    ),
    n_results: int = Query(
        DEFAULT_RESULTS,
        description='Number of results to output',
        ge=MIN_RESULTS,
        le=MAX_RESULTS,
    ),
):
    """
    Retrieve taxi trips starting from a specified timestamp.

    Args:
        from_ms: Unix timestamp in milliseconds (between 2000-01-01 and 2100-01-01)
        n_results: Number of results to return (between 1 and 10000)

    Returns:
        TripsResponse with list of trips and pagination info
    """
    logger.info(
        f'Received request with params from_ms: {from_ms}, n_results: {n_results}'
    )

    try:
        # Get the trips from the backend
        trips: list[Trip] = get_trips(from_ms, n_results)

        # Format the response object TripsResponse
        if len(trips) > 0:
            return TripsResponse(
                trips=trips,
                next_from_ms=trips[-1].tpep_pickup_datetime_ms,
                message=f'Success. Returned {len(trips)} trips.',
            )
        else:
            return TripsResponse(message='No trips found for the given time range.')
    except ValueError as e:
        logger.error(f'Value error in get_trip: {e}')
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f'Unexpected error in get_trip: {e}')
        raise HTTPException(
            status_code=500, detail='An internal error occurred while processing the request'
        )


@app.get(
    '/health',
    tags=['health'],
    summary='Health check endpoint',
    description='Returns the health status of the API',
)
def health_check():
    """
    Health check endpoint to verify the API is running.

    Returns:
        Status object indicating API health
    """
    return {'status': 'Healthy!!!'}
