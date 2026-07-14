from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file= '.env', extra='ignore')
    
    database_url: str
    ckan_base_url: str
    resource_id: str
    ingest_limit: int
    ingest_interval: int
    max_pages: int = 100
    
#self note: python imports a module once and caches it, so every file 
#importing settings gets the same object. One object shared across imports,
#as long as you only instantiate it once at module level
settings = Settings()
