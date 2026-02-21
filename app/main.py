from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# =====================================================
# INITIALIZE APP FIRST
# =====================================================

app = FastAPI(
    title="VoyageOS API",
    version="4.2.3"
)

# =====================================================
# 🔥 CORS MUST BE FIRST MIDDLEWARE
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TEMPORARY FULL OPEN FOR DEBUG
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# IMPORT AFTER APP CREATION
# =====================================================

from app.database import engine
from app import models
from app.dependencies import get_current_user
from app.auth import router as auth_router

from app.routers.clients import router as clients_router
from app.routers.countries import router as countries_router
from app.routers.cities import router as cities_router
from app.routers.services import router as services_router
from app.routers.vendors import router as vendors_router
from app.routers.service_rates import router as service_rates_router
from app.routers.quotations import router as quotations_router
from app.routers.quotation_items import router as quotation_items_router
from app.routers.invoices import router as invoices_router
from app.routers.dashboard import router as dashboard_router
from app.routers.payments import router as payments_router
from app.routers.accounts import router as accounts_router

# =====================================================
# STATIC
# =====================================================

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# =====================================================
# ROUTERS
# =====================================================

app.include_router(auth_router)

app.include_router(clients_router, dependencies=[Depends(get_current_user)])
app.include_router(countries_router, dependencies=[Depends(get_current_user)])
app.include_router(cities_router, dependencies=[Depends(get_current_user)])
app.include_router(services_router, dependencies=[Depends(get_current_user)])
app.include_router(vendors_router, dependencies=[Depends(get_current_user)])
app.include_router(service_rates_router, dependencies=[Depends(get_current_user)])
app.include_router(quotations_router, dependencies=[Depends(get_current_user)])
app.include_router(quotation_items_router, dependencies=[Depends(get_current_user)])
app.include_router(invoices_router, dependencies=[Depends(get_current_user)])
app.include_router(dashboard_router, dependencies=[Depends(get_current_user)])
app.include_router(payments_router, dependencies=[Depends(get_current_user)])
app.include_router(accounts_router, dependencies=[Depends(get_current_user)])

# =====================================================
# ROOT
# =====================================================

@app.get("/")
def root():
    return {
        "status": "running",
        "version": "4.2.3",
        "message": "VoyageOS ERP Engine Running 🔐"
    }
