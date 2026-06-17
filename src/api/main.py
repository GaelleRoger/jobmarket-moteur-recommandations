from fastapi import FastAPI
from .routes.health import router as health_router
from .routes.search import router as search_router
from .routes.jobs import router as jobs_router
from .routes.stats import router as stats_router
from .routes.ml import router as ml_router
 
app = FastAPI(title="Job Market API")
app.include_router(health_router)
app.include_router(search_router)
app.include_router(jobs_router)
app.include_router(stats_router)
app.include_router(ml_router)

