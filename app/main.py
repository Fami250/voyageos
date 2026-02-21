from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# =====================================================
# INITIALIZE APP
# =====================================================

app = FastAPI(
    title="VoyageOS API",
    version="4.2.4"
)

# =====================================================
# CORS (KEEP FIRST)
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Debug mode open
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# IMPORT AFTER APP CREATION
# =====================================================

from app.database import engine
from app import models

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
# STATIC FILES
# =====================================================

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# =====================================================
# ROUTERS
# =====================================================

# Auth (public)
app.include_router(auth_router)

# All other routers manage their own protection internally
app.include_router(clients_router)
app.include_router(countries_router)
app.include_router(cities_router)
app.include_router(services_router)
app.include_router(vendors_router)
app.include_router(service_rates_router)
app.include_router(quotations_router)
app.include_router(quotation_items_router)
app.include_router(invoices_router)
app.include_router(dashboard_router)
app.include_router(payments_router)
app.include_router(accounts_router)

# =====================================================
# ROOT
# =====================================================

@app.get("/")
def root():
    return {
        "status": "running",
        "version": "4.2.4",
        "message": "VoyageOS ERP Engine Running 🚀"
    }
