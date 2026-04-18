from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Dono routers ko ek saath import karo
from places import router as places_router
from agent import router as agent_router

app = FastAPI(title="KhojIndia API Engine")

# =====================================================================
# 🛡️ CORS MIDDLEWARE (Isse lagane se 'Blocked' errors nahi aayenge)
# =====================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Sabhi origins (React, Mobile, etc.) ko allow karo
    allow_credentials=True,
    allow_methods=["*"], # GET, POST, etc. sab allow
    allow_headers=["*"],
)

# =====================================================================
# 🚀 ROUTERS REGISTRATION
# =====================================================================
# Sabhi connections yahan se honge
app.include_router(places_router, tags=["Places"])
app.include_router(agent_router, tags=["Agent"])

@app.get("/")
def home():
    return {
        "status": "KhojIndia Backend is Flying! 🚀",
        "docs": "Go to /docs for API documentation"
    }