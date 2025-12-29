import time
from datetime import datetime
from typing import Optional

from elasticsearch import Elasticsearch
from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import elasticsearch_config

# Initialize Elasticsearch client with connection pooling and retry logic
_es_client: Optional[Elasticsearch] = None


def get_elasticsearch_client() -> Optional[Elasticsearch]:
    """Get or create Elasticsearch client with lazy initialization."""
    global _es_client
    
    # Check if Elasticsearch is enabled
    if not elasticsearch_config.enabled:
        return None
    
    if _es_client is None:
        try:
            _es_client = Elasticsearch(
                [elasticsearch_config.host],
                max_retries=3,
                retry_on_timeout=True,
                request_timeout=5,
            )
            # Test connection
            if not _es_client.ping():
                logger.warning('Elasticsearch connection failed, logging disabled')
                _es_client = None
        except Exception as e:
            logger.warning(f'Failed to initialize Elasticsearch client: {e}')
            _es_client = None
    return _es_client


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == '/trips':
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log to Elasticsearch (non-blocking, fails gracefully)
            es = get_elasticsearch_client()
            if es is not None:
                try:
                    es.index(
                        index=elasticsearch_config.index,
                        body={
                            'endpoint': '/trips',
                            'method': request.method,
                            'process_time': process_time,
                            'status_code': response.status_code,
                            'timestamp': datetime.utcnow().isoformat(),
                        },
                    )
                except Exception as e:
                    logger.debug(f'Error logging to Elasticsearch: {e}')

            return response

        return await call_next(request)
