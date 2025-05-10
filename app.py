import os
from flask import Flask, jsonify
from flask_cors import CORS
from api.recommender import recommender_bp
from config.config import Config

def create_app(config=Config):
    """Create and configure the Flask app"""
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Enable CORS for all origins (can be restricted in production)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register blueprint
    app.register_blueprint(recommender_bp, url_prefix='/api')
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy', 
            'version': '1.0.0',
            'service': 'Finergize Recommender API'
        }), 200
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)