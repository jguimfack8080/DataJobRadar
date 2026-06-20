"""Aggregierter v1-Router."""
from fastapi import APIRouter

from backend.app.api.v1 import cities, companies, jobs, skills, stats, trends

router = APIRouter()
router.include_router(jobs.router)
router.include_router(stats.router)
router.include_router(skills.router)
router.include_router(companies.router)
router.include_router(cities.router)
router.include_router(trends.router)
