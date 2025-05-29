from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn
from datetime import datetime
import logging

from agents.orchestrator import ClaimProcessingOrchestrator
from models.schemas import ClaimProcessingResponse
from utils.file_handler import FileHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HealthPay Multi-Agent Claim Processor",
    description="AI-driven medical insurance claim processing with specialized agents",
    version="1.0.0-multi-agent"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = ClaimProcessingOrchestrator()

@app.get("/")
async def root():
    return {
        "message": "HealthPay Multi-Agent AI Claim Processor",
        "status": "active",
        "architecture": "multi-agent",
        "agents": [
            "DocumentClassifierAgent",
            "TextExtractionAgent", 
            "BillProcessingAgent",
            "DischargeProcessingAgent",
            "ValidationAgent",
            "DecisionAgent"
        ]
    }

@app.post("/process-claim", response_model=ClaimProcessingResponse)
async def process_claim(files: List[UploadFile] = File(...)):
    try:
        logger.info(f"🤖 Processing {len(files)} files with Multi-Agent System")
        
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Process through agent orchestrator
        result = await orchestrator.process_claim_documents(files)
        
        logger.info("✅ Multi-agent processing completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"💥 Multi-agent processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "architecture": "multi-agent",
        "ai_enabled": True,
        "agents_active": 6,
        "model": "gemini-1.5-flash"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
