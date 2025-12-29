import os
from pydantic import Field
from pydantic_settings import BaseSettings


class ElasticsearchConfig(BaseSettings):
    host: str = Field(default='http://localhost:9200', alias='ELASTICSEARCH_HOST')
    index: str = Field(default='taxi_data_api', alias='ELASTICSEARCH_INDEX')
    enabled: bool = Field(default=True, alias='ELASTICSEARCH_ENABLED')

    class Config:
        env_file = '.env'
        case_sensitive = False


class AppConfig(BaseSettings):
    cache_dir: str = Field(
        default='/tmp/taxi-data-api-python/', alias='CACHE_DIR'
    )
    max_cache_size: int = Field(default=10, alias='MAX_CACHE_SIZE')
    download_timeout: int = Field(default=30, alias='DOWNLOAD_TIMEOUT')

    class Config:
        env_file = '.env'
        case_sensitive = False


elasticsearch_config = ElasticsearchConfig()
app_config = AppConfig()
