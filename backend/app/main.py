from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.auth import router as auth_router
from backend.app.questions import router as questions_router
from backend.app.submissions import router as submissions_router
from backend.app.evaluations import router as evaluations_router
from backend.app.config import validate_config

# Run configuration check on startup
validate_config()

app = FastAPI(title="PromptBench API", version="1.0.0")

# CORS middleware configuration
# For production deployment, you would change these origins to match your domain
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers under /api
app.include_router(auth_router, prefix="/api")
app.include_router(questions_router, prefix="/api")
app.include_router(submissions_router, prefix="/api")
app.include_router(evaluations_router, prefix="/api")

@app.get("/api/health")
def health():
    return {"status": "ok", "message": "PromptBench backend is running"}
