import os
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from services.recommender_service import RecommenderService
from config.config import config_by_name

# Create FastAPI app
app = FastAPI(
    title="Finergize Recommender API",
    description="API for personalized financial feature recommendations",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Global service instance
_service = None

def get_service():
    """Get or create recommender service instance"""
    global _service
    if _service is None:
        _service = RecommenderService()
    return _service

class SurveyResponse(BaseModel):
    """Model for survey responses"""
    responses: Dict[str, Any]

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "Finergize Recommender API"
    }

@app.get("/api/survey")
def get_survey(
    location: str = Query("Delhi NCR", description="User's location in India"),
    age: str = Query("25-34", description="User's age group"),
    interest: str = Query("General", description="Primary financial interest"),
    literacy_level: str = Query("moderate", description="Level of financial literacy")
):
    """Get personalized survey questions"""
    try:
        user_context = {
            'location': location,
            'age': age,
            'interest': interest,
            'literacy_level': literacy_level
        }
        
        service = get_service()
        survey_questions = service.generate_survey(user_context)
        
        return {
            'success': True,
            'survey': survey_questions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommend")
def recommend_features(
    survey_response: SurveyResponse, 
    service: RecommenderService = Depends(get_service)
):
    """Generate personalized feature recommendations"""
    try:
        recommendations = service.recommend_features(survey_response.responses)
        
        return {
            'success': True,
            'recommendations': recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/features")
def get_features(service: RecommenderService = Depends(get_service)):
    """Get all available Finergize features"""
    try:
        features = service.get_features()
        
        return {
            'success': True,
            'features': features
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Determine environment
    env = os.environ.get('ENV', 'development')
    config = config_by_name.get(env, config_by_name['development'])
    
    # Run server
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=config.DEBUG)