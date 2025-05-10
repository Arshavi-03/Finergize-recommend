import os
import json
import joblib
import logging
import openai
from typing import Dict, Any, List

class RecommenderService:
    """Service for feature recommendation operations"""
    
    def __init__(self, model_path=None):
        """Initialize the recommender service"""
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.has_api = False
        
        # Configure logging
        logging.basicConfig(level=logging.INFO, 
                             format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Load model
        self.load_model(model_path)
        
        # Configure OpenAI API key
        self.configure_openai()
    
    def configure_openai(self):
        """Configure OpenAI API key"""
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        use_openai = os.environ.get('USE_OPENAI', 'True').lower() == 'true'
        
        if use_openai and openai_api_key:
            try:
                openai.api_key = openai_api_key
                self.has_api = True
                self.logger.info("OpenAI API configured successfully")
            except Exception as e:
                self.logger.error(f"Error configuring OpenAI API: {e}")
                self.has_api = False
        else:
            self.logger.warning("OpenAI integration is disabled or API key not provided")
    
    def load_model(self, model_path=None):
        """Load the recommender model"""
        # Use provided path or default
        model_path = model_path or os.environ.get(
            'MODEL_PATH', 
            'models/finergize_recommender_agent_clean.joblib'
        )
        
        try:
            self.logger.info(f"Loading model from {model_path}")
            
            # Load the model
            with open(model_path, 'rb') as f:
                self.model = joblib.load(f)
            
            self.logger.info("Model loaded successfully")
        
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            # Fallback to creating a default model
            self.model = self._create_default_model()
    
    def _create_default_model(self):
        """Create a default model with basic configurations"""
        from types import SimpleNamespace
        
        # Create a simple namespace to mimic model structure
        default_model = SimpleNamespace(
            finergize_features={
                "digital_banking": {
                    "name": "Digital Banking",
                    "description": "Secure digital banking services"
                }
                # Add other default features
            },
            question_templates={},
            has_api=False
        )
        
        return default_model
    
    def generate_survey(self, user_context):
        """Generate survey questions"""
        try:
            if hasattr(self.model, 'generate_survey'):
                return self.model.generate_survey(user_context)
            else:
                # Fallback survey generation
                return self._generate_default_survey()
        except Exception as e:
            self.logger.error(f"Survey generation error: {e}")
            return self._generate_default_survey()
    
    def _generate_default_survey(self):
        """Create a default survey if model method is unavailable"""
        return [
            {
                "id": "financial_goals",
                "question": "What are your primary financial goals?",
                "type": "multiple-choice",
                "options": [
                    {"id": "save", "text": "Save for emergencies"},
                    {"id": "invest", "text": "Invest for growth"}
                ]
            }
        ]
    
    def recommend_features(self, responses):
        """Recommend features based on survey responses"""
        try:
            if hasattr(self.model, 'recommend_features'):
                return self.model.recommend_features(responses)
            else:
                # Fallback recommendation logic
                return self._generate_default_recommendations(responses)
        except Exception as e:
            self.logger.error(f"Feature recommendation error: {e}")
            return self._generate_default_recommendations(responses)
    
    def _generate_default_recommendations(self, responses):
        """Generate default recommendations"""
        return {
            "prioritized_features": [
                {
                    "id": "digital_banking",
                    "name": "Digital Banking",
                    "score": 8,
                    "explanation": "Core digital banking services",
                    "tip": "Start with basic digital banking features"
                }
            ],
            "user_profile": {
                "knowledge_level": "beginner",
                "income_level": "Not specified"
            }
        }
    
    def get_features(self):
        """Get all available Finergize features"""
        try:
            if hasattr(self.model, 'finergize_features'):
                return self.model.finergize_features
            else:
                return {}
        except Exception as e:
            self.logger.error(f"Error retrieving features: {e}")
            return {}