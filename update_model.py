import os
import sys
import joblib
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the FinergizeRecommenderAgent class to ensure it exists in this context
class FinergizeRecommenderAgent:
    """
    Agentic AI system that recommends and prioritizes Finergize features
    based on user survey responses.
    """
    def __init__(self, openai_api_key=None):
        self.api_key = openai_api_key
        self.has_api = openai_api_key is not None
        
        # Define the Finergize features
        self.finergize_features = {
            "digital_banking": {
                "name": "Digital Banking",
                "description": "Secure digital banking services with UPI payments, bill payments, and account management",
                "ideal_for": "Users looking for convenient, modern banking with minimal fees"
            },
            "mutual_funds": {
                "name": "Mutual Funds",
                "description": "Simple investments in diversified mutual funds with low minimum entry",
                "ideal_for": "Users interested in growing their wealth through market-linked investments"
            },
            "community_savings": {
                "name": "Community Savings",
                "description": "Group savings programs where community members save together and support each other",
                "ideal_for": "Users who want to save with friends, family or community members for shared goals"
            },
            "micro_loans": {
                "name": "Micro Loans",
                "description": "Small, accessible loans with simple application process and fair interest rates",
                "ideal_for": "Users needing small amounts of credit for business or personal needs"
            },
            "analytics_profile": {
                "name": "Analytics Profile",
                "description": "Personalized financial insights and spending analysis to improve financial management",
                "ideal_for": "Users who want to understand their spending patterns and improve budgeting"
            },
            "financial_education": {
                "name": "Financial Education",
                "description": "Courses, articles and workshops on financial literacy and management",
                "ideal_for": "Users looking to improve their financial knowledge and decision-making"
            }
        }
        
        # Base question templates
        self.question_templates = {
            "financial_goals": {
                "id": "financial_goals",
                "question": "What are your primary financial goals?",
                "type": "multiple-choice",
                "options": [
                    {"id": "save", "text": "Save for emergencies"},
                    {"id": "invest", "text": "Invest for long-term growth"},
                    {"id": "loan", "text": "Get a small loan for specific needs"},
                    {"id": "education", "text": "Learn more about financial management"},
                    {"id": "community", "text": "Save with family or community members"},
                    {"id": "track", "text": "Track and manage my spending better"}
                ],
                "allowMultiple": True
            },
            "income_range": {
                "id": "income_range",
                "question": "What is your monthly income range?",
                "type": "single-choice",
                "options": [
                    {"id": "income_low", "text": "Below ₹15,000"},
                    {"id": "income_medium_low", "text": "₹15,000 - ₹30,000"},
                    {"id": "income_medium", "text": "₹30,000 - ₹60,000"},
                    {"id": "income_medium_high", "text": "₹60,000 - ₹1,20,000"},
                    {"id": "income_high", "text": "Above ₹1,20,000"}
                ]
            },
            "financial_knowledge": {
                "id": "financial_knowledge",
                "question": "How would you rate your financial knowledge?",
                "type": "single-choice",
                "options": [
                    {"id": "beginner", "text": "Beginner - I know very little"},
                    {"id": "basic", "text": "Basic - I understand fundamental concepts"},
                    {"id": "intermediate", "text": "Intermediate - I can make informed decisions"},
                    {"id": "advanced", "text": "Advanced - I understand complex financial products"}
                ]
            },
            "banking_habits": {
                "id": "banking_habits",
                "question": "How do you currently do most of your banking?",
                "type": "single-choice",
                "options": [
                    {"id": "traditional", "text": "Traditional bank branches"},
                    {"id": "atm", "text": "ATMs"},
                    {"id": "net_banking", "text": "Net banking on computer"},
                    {"id": "mobile", "text": "Mobile banking apps"},
                    {"id": "upi", "text": "UPI apps (Google Pay, PhonePe, etc.)"},
                    {"id": "limited", "text": "I have limited banking access"}
                ]
            },
            "savings_method": {
                "id": "savings_method",
                "question": "How do you currently save money?",
                "type": "multiple-choice",
                "options": [
                    {"id": "bank", "text": "Bank savings account"},
                    {"id": "cash", "text": "Cash at home"},
                    {"id": "fd", "text": "Fixed deposits"},
                    {"id": "post", "text": "Post office schemes"},
                    {"id": "chit", "text": "Chit funds/community savings"},
                    {"id": "gold", "text": "Gold/jewelry"},
                    {"id": "mutual_funds", "text": "Mutual funds"},
                    {"id": "stocks", "text": "Direct stocks"},
                    {"id": "no_savings", "text": "I don't save regularly"}
                ],
                "allowMultiple": True
            },
            "loan_needs": {
                "id": "loan_needs",
                "question": "Do you currently need or expect to need a small loan?",
                "type": "single-choice",
                "options": [
                    {"id": "current", "text": "Yes, I currently need a small loan"},
                    {"id": "future", "text": "Not now, but might in the near future"},
                    {"id": "no", "text": "No, I don't expect to need a loan"}
                ]
            },
            "digital_comfort": {
                "id": "digital_comfort",
                "question": "How comfortable are you using digital/mobile financial apps?",
                "type": "single-choice",
                "options": [
                    {"id": "very", "text": "Very comfortable - I use multiple apps regularly"},
                    {"id": "somewhat", "text": "Somewhat comfortable - I use basic features"},
                    {"id": "limited", "text": "Limited comfort - I use them with help"},
                    {"id": "uncomfortable", "text": "Uncomfortable - I prefer not to use them"}
                ]
            },
            "tracking_interest": {
                "id": "tracking_interest",
                "question": "How interested are you in tracking and analyzing your spending habits?",
                "type": "slider",
                "min": 1,
                "max": 5,
                "labels": {
                    "1": "Not Interested",
                    "3": "Somewhat Interested",
                    "5": "Very Interested"
                }
            }
        }
        
        # Chat history for maintaining context with OpenAI
        self.chat_history = [
            {"role": "system", "content": """You are a specialized financial advisor AI for Finergize, an Indian financial platform with six key features:
1. Digital Banking - Modern mobile banking services
2. Mutual Funds - Simple investment options
3. Community Savings - Group-based savings programs
4. Micro Loans - Small, accessible loans
5. Analytics Profile - Personal financial insights
6. Financial Education - Learning resources

Your goal is to recommend the most suitable Finergize features based on user survey responses. Prioritize features that best match their needs."""}
        ]
    
    def generate_survey(self, user_context):
        """Generate a personalized financial survey based on user context"""
        # Base implementation
        questions = []
        
        # Core questions everyone gets
        questions.append(self.question_templates["financial_goals"])
        questions.append(self.question_templates["income_range"])
        questions.append(self.question_templates["financial_knowledge"])
        questions.append(self.question_templates["banking_habits"])
        questions.append(self.question_templates["savings_method"])
        questions.append(self.question_templates["loan_needs"])
        questions.append(self.question_templates["digital_comfort"])
        questions.append(self.question_templates["tracking_interest"])
        
        return questions
        
    def recommend_features(self, responses):
        """Process survey responses and generate recommendations"""
        # This would normally call OpenAI, but since we're just creating a skeleton,
        # we'll delegate to the fallback method
        return self.generate_fallback_recommendations(responses)
    
    def generate_fallback_recommendations(self, responses):
        """Generate basic feature recommendations as a fallback"""
        # Extract key information from responses
        goals = responses.get("financial_goals", [])
        if not isinstance(goals, list):
            goals = [goals]
            
        banking_habit = responses.get("banking_habits", "traditional")
        savings_methods = responses.get("savings_method", [])
        if not isinstance(savings_methods, list):
            savings_methods = [savings_methods]
            
        loan_need = responses.get("loan_needs", "no")
        digital_comfort = responses.get("digital_comfort", "somewhat")
        tracking_interest = responses.get("tracking_interest", 3)
        knowledge_level = responses.get("financial_knowledge", "beginner")
        
        # Calculate relevance scores for each feature
        feature_scores = {
            "digital_banking": 5,
            "mutual_funds": 5,
            "community_savings": 5,
            "micro_loans": 5,
            "analytics_profile": 5,
            "financial_education": 5
        }
        
        # Adjust scores based on responses
        
        # Digital Banking relevance
        if digital_comfort in ["very", "somewhat"]:
            feature_scores["digital_banking"] += 3
        if banking_habit in ["mobile", "upi", "net_banking"]:
            feature_scores["digital_banking"] += 2
        if banking_habit in ["traditional", "atm", "limited"]:
            feature_scores["digital_banking"] += 1
        
        # Mutual Funds relevance
        if "invest" in goals:
            feature_scores["mutual_funds"] += 3
        if "mutual_funds" in savings_methods:
            feature_scores["mutual_funds"] += 2
        if knowledge_level in ["intermediate", "advanced"]:
            feature_scores["mutual_funds"] += 1
        
        # Community Savings relevance
        if "community" in goals:
            feature_scores["community_savings"] += 3
        if "chit" in savings_methods:
            feature_scores["community_savings"] += 3
        if "save" in goals:
            feature_scores["community_savings"] += 1
        
        # Micro Loans relevance
        if loan_need in ["current", "future"]:
            feature_scores["micro_loans"] += 4
        if "loan" in goals:
            feature_scores["micro_loans"] += 3
        
        # Analytics Profile relevance
        if "track" in goals:
            feature_scores["analytics_profile"] += 3
        if isinstance(tracking_interest, (int, float)) and tracking_interest >= 4:
            feature_scores["analytics_profile"] += 3
        elif isinstance(tracking_interest, (int, float)) and tracking_interest >= 3:
            feature_scores["analytics_profile"] += 1
        
        # Financial Education relevance
        if "education" in goals:
            feature_scores["financial_education"] += 4
        if knowledge_level in ["beginner", "basic"]:
            feature_scores["financial_education"] += 2
        
        # Ensure scores are within 1-10 range
        for feature in feature_scores:
            feature_scores[feature] = max(1, min(10, feature_scores[feature]))
        
        # Create explanation and tips for each feature
        feature_details = {}
        
        # Digital Banking
        feature_details["digital_banking"] = {
            "explanation": "Modern banking services for easy money management via mobile.",
            "tip": "Start with basic UPI payments and bill payments to get comfortable."
        }
        
        # Mutual Funds
        feature_details["mutual_funds"] = {
            "explanation": "Simple investment options to grow your wealth over time.",
            "tip": "Begin with a SIP (Systematic Investment Plan) with as little as ₹500 per month."
        }
        
        # Community Savings
        feature_details["community_savings"] = {
            "explanation": "Save together with family or community members for shared goals.",
            "tip": "Create a savings group with 5-10 trusted people you know."
        }
        
        # Micro Loans
        feature_details["micro_loans"] = {
            "explanation": "Small loans for personal or business needs with simple application.",
            "tip": "Start with a small loan amount to build your credit profile."
        }
        
        # Analytics Profile
        feature_details["analytics_profile"] = {
            "explanation": "Track your spending and get personalized insights to manage money better.",
            "tip": "Link your accounts to get a complete picture of your finances."
        }
        
        # Financial Education
        feature_details["financial_education"] = {
            "explanation": "Learn essential financial skills through courses and articles.",
            "tip": "Start with the basic modules on budgeting and saving."
        }
        
        # Create prioritized feature list
        prioritized_features = []
        for feature_id, score in sorted(feature_scores.items(), key=lambda x: x[1], reverse=True):
            prioritized_features.append({
                "id": feature_id,
                "name": self.finergize_features[feature_id]["name"],
                "score": score,
                "explanation": feature_details[feature_id]["explanation"],
                "tip": feature_details[feature_id]["tip"]
            })
        
        # Return final recommendations
        return {
            "prioritized_features": prioritized_features,
            "user_profile": {
                "knowledge_level": knowledge_level,
                "income_level": self.map_income_level(responses.get("income_range", "income_medium"))
            }
        }
    
    def map_income_level(self, income_range):
        """Map income range ID to display text"""
        income_map = {
            "income_low": "Below ₹15,000",
            "income_medium_low": "₹15,000 - ₹30,000",
            "income_medium": "₹30,000 - ₹60,000",
            "income_medium_high": "₹60,000 - ₹1,20,000",
            "income_high": "Above ₹1,20,000"
        }
        return income_map.get(income_range, "₹30,000 - ₹60,000")

def create_fresh_model(output_path):
    """Create a fresh model file"""
    logger.info(f"Creating a fresh model file at {output_path}")
    
    # Create a new instance without API key
    model = FinergizeRecommenderAgent(None)
    
    # Set has_api to True to indicate it supports OpenAI
    model.has_api = True
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Save the model
    joblib.dump(model, output_path)
    logger.info(f"Model saved to {output_path}")
    return True

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Update or create Finergize recommender model')
    parser.add_argument('--create', action='store_true', help='Create a new model file')
    parser.add_argument('--update', action='store_true', help='Update an existing model file')
    parser.add_argument('--input', type=str, help='Input model file path (for update)')
    parser.add_argument('--output', type=str, required=True, help='Output model file path')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.create and args.update:
        logger.error("Cannot specify both --create and --update")
        sys.exit(1)
    
    if not (args.create or args.update):
        logger.error("Must specify either --create or --update")
        sys.exit(1)
    
    if args.update and not args.input:
        logger.error("Must specify --input when using --update")
        sys.exit(1)
    
    # Execute requested action
    if args.create:
        success = create_fresh_model(args.output)
    else:  # update
        success = update_existing_model(args.input, args.output)
    
    if success:
        logger.info("Operation completed successfully")
        sys.exit(0)
    else:
        logger.error("Operation failed")
        sys.exit(1)


def update_existing_model(input_path, output_path):
    """Update an existing model file"""
    logger.info(f"Updating model from {input_path} to {output_path}")
    
    # First check if the file exists
    if not os.path.exists(input_path):
        logger.error(f"Input model file not found: {input_path}")
        return False
        
    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    try:
        # Try to load with standard joblib
        model = joblib.load(input_path)
        logger.info("Successfully loaded model with standard joblib")
    except (AttributeError, ImportError) as e:
        logger.warning(f"Standard loading failed: {e}. Trying custom unpickler...")
        
        class CustomUnpickler(joblib.numpy_pickle.NumpyUnpickler):
            def find_class(self, module, name):
                # Handle the FinergizeRecommenderAgent class
                if name == 'FinergizeRecommenderAgent':
                    return FinergizeRecommenderAgent
                # For all other classes, use the default behavior
                return super().find_class(module, name)
        
        try:
            with open(input_path, 'rb') as f:
                model = CustomUnpickler(f).load()
            logger.info("Successfully loaded model with custom unpickler")
        except Exception as e:
            logger.error(f"Custom unpickler failed: {e}")
            return False
    
    # Update model attributes to ensure compatibility
    logger.info("Updating model attributes...")
    
    # Check if finergize_features exists and copy if needed
    if not hasattr(model, 'finergize_features') or not model.finergize_features:
        model.finergize_features = FinergizeRecommenderAgent().finergize_features
        logger.info("Added finergize_features to model")
    
    # Check if question_templates exists and copy if needed
    if not hasattr(model, 'question_templates') or not model.question_templates:
        model.question_templates = FinergizeRecommenderAgent().question_templates
        logger.info("Added question_templates to model")
    
    # Check if chat_history exists and copy if needed
    if not hasattr(model, 'chat_history') or not model.chat_history:
        model.chat_history = FinergizeRecommenderAgent().chat_history
        logger.info("Added chat_history to model")
        
    # Ensure has_api is True and api_key is None (will be injected at runtime)
    model.has_api = True
    model.api_key = None
    logger.info("Updated API settings: has_api=True, api_key=None")
    
    # Save the updated model
    joblib.dump(model, output_path)
    logger.info(f"Updated model saved to {output_path}")
    return True