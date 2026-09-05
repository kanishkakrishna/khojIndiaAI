from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
# Import the API router.
from places import router as places_router

app = FastAPI(title="KhojIndia API Engine")

# =====================================================================
# CORS MIDDLEWARE
# =====================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow requests from all origins, including web and mobile clients.
    allow_credentials=True,
    allow_methods=["*"], # Allow all HTTP methods.
    allow_headers=["*"],
)

# =====================================================================
# ROUTER REGISTRATION
# =====================================================================
# Register all place-related API routes.
app.include_router(places_router, tags=["Places"])

@app.get("/")
def home():
    return {
        "status": "KhojIndia Backend is Flying! 🚀",
        "docs": "Go to /docs for API documentation"
    }