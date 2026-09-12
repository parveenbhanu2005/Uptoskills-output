import os
import json
import cv2
import numpy as np
import torch
import ultralytics
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from backend.inference.pipeline import InspectionPipeline
from backend.database.repository import InspectionRepository
from backend.utils.logger import setup_logger

logger = setup_logger("inference_router")

router = APIRouter(prefix="/api", tags=["inference"])
pipeline = InspectionPipeline()
repo = InspectionRepository()


class DetectionItem(BaseModel):
    detection_id: int
    class_id: int
    class_name: str
    confidence: float
    bbox: List[float]


class NormalizedDetectionItem(BaseModel):
    detection_id: int
    class_id: int
    class_name: str
    confidence: float
    bbox: Any # dict or list
    severity_score: float
    severity_level: str
    recommended_action: str
    ticket_id: Optional[str] = None
    crop_path: Optional[str] = None


class MaintenanceTicketItem(BaseModel):
    ticket_id: str
    inspection_id: str
    detection_id: int
    class_name: str
    confidence: float
    severity_score: float
    severity_level: str
    priority: str
    recommended_action: str
    status: str
    reason: str
    created_at: str


class TicketStatusUpdateRequest(BaseModel):
    status: str


class InferenceStatistics(BaseModel):
    total_detections: int
    class_distribution: Dict[str, int]
    average_confidence: float
    highest_confidence: float
    lowest_confidence: float
    inference_time_ms: float
    model_filename: str
    device: str
    input_resolution: str


class InferenceResponse(BaseModel):
    inspection_id: str
    image_id: str
    model: str
    device: str
    input_resolution: str
    original_image: str
    annotated_image: str
    csv: str
    pdf: str
    detections_json: str
    detections: List[DetectionItem]
    normalized_detections: Optional[List[NormalizedDetectionItem]] = []
    severity_summary: Optional[Dict[str, int]] = {}
    maintenance_summary: Optional[Dict[str, int]] = {}
    tickets: Optional[List[MaintenanceTicketItem]] = []
    count: int
    time_ms: float
    processing_time_ms: float
    statistics: InferenceStatistics
    masks: List[Dict[str, Any]]
    classifications: Dict[str, Any]
    severity_scores: Dict[str, Any]
    status: str


@router.get("/health")
def health_check():
    try:
        model_loaded = pipeline.detector.loaded
        model_info = pipeline.detector.get_model_info()

        return {
            "status": "healthy",
            "model_loaded": model_loaded,
            "model_name": model_info["filename"],
            "model_path": model_info["path"],
            "device": model_info["device"],
            "imgsz": model_info["imgsz"],
            "ultralytics_version": ultralytics.__version__,
            "torch_version": torch.__version__
        }
    except Exception as e:
        logger.error(f"Health check diagnostics error: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.post("/infer")
async def run_inference(
    file: UploadFile = File(...),
    preprocessing_config: Optional[str] = Form(None)
):
    logger.info(f"Received inference request for file: {file.filename}")

    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.tif')):
        logger.error(f"Unsupported file format rejected: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Only JPG, PNG, and TIFF are supported."
        )

    config = {}
    if preprocessing_config:
        try:
            config = json.loads(preprocessing_config)
        except Exception as e:
            logger.error(f"Failed to parse preprocessing_config JSON: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid preprocessing_config JSON format: {str(e)}"
            )

    try:
        image_bytes = await file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            logger.error(f"Failed to decode image: {file.filename}")
            raise HTTPException(
                status_code=400,
                detail="Failed to decode uploaded image. The file may be corrupted or invalid."
            )

        result = pipeline.run(
            img,
            image_id=file.filename,
            preprocessing_config=config,
            original_image_bytes=image_bytes
        )
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Pipeline execution encountered error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal inference engine execution failure: {str(e)}"
        )


@router.get("/tickets")
def get_tickets(status: Optional[str] = Query(None)):
    """Retrieve maintenance tickets, optionally filtered by status ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')."""
    try:
        tickets = repo.get_tickets(status=status)
        return {"success": True, "tickets": tickets}
    except Exception as e:
        logger.error(f"Failed to fetch maintenance tickets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/tickets/{ticket_id}/status")
def update_ticket_status(ticket_id: str, payload: TicketStatusUpdateRequest):
    """Update status of a maintenance ticket ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')."""
    try:
        success = repo.update_ticket_status(ticket_id, payload.status)
        if not success:
            raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")
        return {"success": True, "ticket_id": ticket_id, "status": payload.status.upper()}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating ticket status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
def get_inspection_history(limit: int = 50):
    """Retrieve recent inspection run records from SQLite database."""
    try:
        history = repo.get_history(limit=limit)
        return {"success": True, "history": history}
    except Exception as e:
        logger.error(f"Failed to fetch inspection history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
