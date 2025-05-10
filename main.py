import os
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from services.recommender_service import RecommenderService

# Create FastAPI app
app = FastAPI(
    title="Finergize Recommender API",
    description="API for personalized financial feature recommendations",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Lazy-loaded service
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
        # Create user context
        user_context = {
            'location': location,
            'age': age,
            'interest': interest,
            'literacy_level': literacy_level
        }
        
        # Get the service and generate survey
        service = get_service()
        survey_questions = service.generate_survey(user_context)
        
        return {
            'success': True,
            'survey': survey_questions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommend")
def recommend_features(survey_response: SurveyResponse, service: RecommenderService = Depends(get_service)):
    """Generate personalized feature recommendations"""
    try:
        # Process recommendations
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

@app.get("/debug")
def debug_info():
    """Debug endpoint to verify configuration"""
    import openai
    from config.config import Config
    
    service = get_service()
    
    # Check API key configuration
    openai_key = os.environ.get('OPENAI_API_KEY', 'Not set')
    openai_key_masked = f"{openai_key[:5]}...{openai_key[-4:]}" if len(openai_key) > 9 else "Not properly set"
    
    openai_module_key = openai.api_key
    openai_module_key_masked = f"{openai_module_key[:5]}...{openai_module_key[-4:]}" if openai_module_key and len(openai_module_key) > 9 else "Not properly set"
    
    # Check model configuration
    model_info = {
        'model_loaded': service.model is not None,
        'model_path': os.environ.get('MODEL_PATH', 'Default path')
    }
    
    if service.model:
        model_info['has_api_attr'] = hasattr(service.model, 'has_api')
        model_info['has_api_value'] = getattr(service.model, 'has_api', None)
        model_info['api_key_attr'] = hasattr(service.model, 'api_key')
        model_info['api_key_set'] = bool(getattr(service.model, 'api_key', None))
        
        if hasattr(service.model, 'api_key') and service.model.api_key:
            model_key = service.model.api_key
            model_info['api_key_masked'] = f"{model_key[:5]}...{model_key[-4:]}" if len(model_key) > 9 else "Invalid format"
    
    # Check if we can make a simple OpenAI call
    openai_test = {}
    try:
        if openai_module_key:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            openai_test['success'] = True
            openai_test['response'] = str(response)
    except Exception as e:
        openai_test['success'] = False
        openai_test['error'] = str(e)
    
    # Return all debug info
    return {
        'environment': {
            'openai_key_configured': bool(openai_key) and openai_key != 'Not set', 
            'openai_key_masked': openai_key_masked,
            'openai_module_key_configured': bool(openai_module_key),
            'openai_module_key_masked': openai_module_key_masked,
            'use_openai': os.environ.get('USE_OPENAI', 'Not set')
        },
        'model_info': model_info,
        'openai_test': openai_test,
        'service_has_api': service.has_api
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)