from flask import Blueprint, request, jsonify
from services.recommender_service import RecommenderService
from api.utils import validate_request

# Create blueprint
recommender_bp = Blueprint('recommender', __name__)

# Initialize service (lazy loading)
_service = None

def get_service():
    """Get or create recommender service instance"""
    global _service
    if _service is None:
        _service = RecommenderService()
    return _service

@recommender_bp.route('/survey', methods=['GET'])
def get_survey():
    """Get the personalized survey questions"""
    try:
        # Get query parameters for user context
        user_context = {
            'location': request.args.get('location', 'Delhi NCR'),
            'age': request.args.get('age', '25-34'),
            'interest': request.args.get('interest', 'General'),
            'literacy_level': request.args.get('literacy_level', 'moderate')
        }
        
        # Get the service and generate survey
        service = get_service()
        survey_questions = service.generate_survey(user_context)
        
        return jsonify({
            'success': True,
            'survey': survey_questions
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@recommender_bp.route('/recommend', methods=['POST'])
def recommend_features():
    """Generate personalized feature recommendations based on survey responses"""
    try:
        # Validate request body
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        # Validate required fields
        if 'responses' not in data:
            return jsonify({
                'success': False,
                'error': 'Survey responses are required'
            }), 400
        
        # Process recommendations
        service = get_service()
        recommendations = service.recommend_features(data['responses'])
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@recommender_bp.route('/features', methods=['GET'])
def get_features():
    """Get all available Finergize features"""
    try:
        service = get_service()
        features = service.get_features()
        
        return jsonify({
            'success': True,
            'features': features
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500