import os
from datetime import datetime
from threading import Lock
from typing import Optional

import pandas as pd
import requests
from loguru import logger
from pydantic import BaseModel

from src.config import app_config

CACHE_DIR = app_config.cache_dir
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR, exist_ok=True)

# In-memory cache for DataFrames to avoid re-reading parquet files
_dataframe_cache: dict[str, pd.DataFrame] = {}
_cache_lock = Lock()
_MAX_CACHE_SIZE = app_config.max_cache_size


class Trip(BaseModel):
    tpep_pickup_datetime: datetime
    tpep_dropoff_datetime: datetime
    trip_distance: float
    fare_amount: float

    @property
    def tpep_pickup_datetime_ms(self) -> int:
        return int(self.tpep_pickup_datetime.timestamp() * 1000)


def get_trips(from_ms: int, n_results: int) -> list[Trip]:
    """
    Returns a list of sorted trips from the given from_ms timestamp, with a maximum of n_results.
    The trips are returned in chronological order.

    Args:
        from_ms: The timestamp in milliseconds to start the search from.
        n_results: The maximum number of results to return.

    Returns:
        A list of trips.
    """
    from src.utils import get_year_and_month

    year, month = get_year_and_month(from_ms)
    logger.info(f'Extracted year: {year}, month: {month}')

    # Load parquet file with the data (uses caching)
    df: Optional[pd.DataFrame] = read_parquet_file(year, month)

    if df is None or df.empty:
        logger.info(f'No trips found for the given year: {year}, month: {month}')
        return []

    # Convert datetime to Unix timestamp in milliseconds (only if not already present)
    if 'tpep_pickup_datetime_ms' not in df.columns:
        # Convert pandas datetime to Unix timestamp in milliseconds
        # Using the same method as original for compatibility
        df['tpep_pickup_datetime_ms'] = (
            df['tpep_pickup_datetime'].astype('int64') / 10**3
        ).astype('int64')

    # Filter df to only include rows where tpep_pickup_datetime_ms is greater than from_ms
    df = df[df['tpep_pickup_datetime_ms'] > from_ms]

    # Get the first n_results rows
    df = df.head(n_results)

    # Convert df to list of Trip objects
    trips = []
    for record in df.to_dict(orient='records'):
        try:
            trips.append(Trip(**record))
        except Exception as e:
            logger.warning(f'Failed to create Trip object: {e}, skipping record')
            continue

    return trips


def download_parquet_file(year: int, month: int) -> bool:
    """
    Download the parquet file for the given year and month from the NYC Taxi and Limousine Commission.

    https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

    Args:
        year: The year to download the file for.
        month: The month to download the file for.

    Returns:
        True if download was successful, False otherwise.
    """
    # URL to download the file from
    url = f'https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year}-{month:02d}.parquet'

    try:
        # Download the file with timeout
        response = requests.get(url, timeout=app_config.download_timeout)
        if response.status_code == 200:
            file_path = f'{CACHE_DIR}/yellow_tripdata_{year}-{month:02d}.parquet'
            with open(file_path, 'wb') as f:
                f.write(response.content)
            logger.info(f'Downloaded file: yellow_tripdata_{year}-{month:02d}.parquet')
            return True
        else:
            logger.error(f'Failed to download file: HTTP {response.status_code}')
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f'Error downloading file: {e}')
        return False


def _get_cache_key(year: int, month: int) -> str:
    """Generate a cache key for the year-month combination."""
    return f'{year}-{month:02d}'


def _manage_cache_size():
    """Remove oldest entries if cache exceeds max size."""
    with _cache_lock:
        if len(_dataframe_cache) >= _MAX_CACHE_SIZE:
            # Remove the first (oldest) entry
            oldest_key = next(iter(_dataframe_cache))
            del _dataframe_cache[oldest_key]
            logger.debug(f'Removed {oldest_key} from cache to maintain size limit')


def read_parquet_file(year: int, month: int) -> Optional[pd.DataFrame]:
    """
    Read the parquet file for the given year and month.
    Uses in-memory caching to avoid re-reading files.

    Args:
        year: The year to read the file for.
        month: The month to read the file for.

    Returns:
        A pandas DataFrame with the data, or None if the file couldn't be read.
    """
    cache_key = _get_cache_key(year, month)

    # Check in-memory cache first
    with _cache_lock:
        if cache_key in _dataframe_cache:
            logger.debug(f'Using cached DataFrame for {cache_key}')
            return _dataframe_cache[cache_key].copy()

    # Check if the file exists on disk
    file_path = f'{CACHE_DIR}/yellow_tripdata_{year}-{month:02d}.parquet'
    if not os.path.exists(file_path):
        logger.info(f'File not found: yellow_tripdata_{year}-{month:02d}.parquet')
        logger.info(f'Downloading file: yellow_tripdata_{year}-{month:02d}.parquet')
        if not download_parquet_file(year, month):
            return None

    logger.info(f'Reading file: yellow_tripdata_{year}-{month:02d}.parquet')
    try:
        df = pd.read_parquet(file_path, engine='pyarrow')
    except Exception as e:
        logger.error(f'Failed to read file: {e}')
        return None

    # Filter the df to only include the columns we need
    required_columns = [
        'tpep_pickup_datetime',
        'tpep_dropoff_datetime',
        'trip_distance',
        'fare_amount',
    ]

    # Check if all required columns exist
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.error(f'Missing required columns: {missing_columns}')
        return None

    df = df[required_columns]

    # Filter rows where tpep_pickup_datetime is in that year and month
    df = df[df['tpep_pickup_datetime'].dt.year == year]
    df = df[df['tpep_pickup_datetime'].dt.month == month]

    # Sort the df by tpep_pickup_datetime
    df = df.sort_values(by='tpep_pickup_datetime').reset_index(drop=True)

    # Cache the processed DataFrame
    _manage_cache_size()
    with _cache_lock:
        _dataframe_cache[cache_key] = df.copy()

    return df.copy()


if __name__ == '__main__':
    # used for debugging purposes
    # import argparse

    # # argparse
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--year", type=int, required=True)
    # parser.add_argument("--month", type=int, required=True)
    # args = parser.parse_args()

    # df = read_parquet_file(args.year, args.month)

    # # df = read_parquet_file(2023, 2)
    # print(df.head())
    # print(df.tail())

    trips = get_trips(from_ms=1674561748000, n_results=100)
