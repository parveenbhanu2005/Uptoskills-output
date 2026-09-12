from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.api import inference_router
from backend.utils.logger import setup_logger

logger = setup_logger("main")

app = FastAPI(
    title="SolarLens AI Inference Service",
    description="Python FastAPI inference microservice for SolarLens AI Inspector",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inference_router)

# Mount outputs directory for serving annotated images, CSVs, etc.
outputs_dir = Path(__file__).resolve().parent / "outputs"
outputs_dir.mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=str(outputs_dir)), name="outputs")
logger.info(f"Static file mount: /outputs -> {outputs_dir}")

@app.get("/")
def root():
    return {"message": "SolarLens Python Inference Service is running", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
