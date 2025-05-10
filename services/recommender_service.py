import os
import json
import joblib
import logging
import pickle

# Try to import the modern OpenAI client
try:
    from openai import OpenAI
    OPENAI_MODERN = True
except ImportError:
    # Fall back to old client if needed
    import openai
    OPENAI_MODERN = False

# Custom unpickler to handle missing classes
class CustomUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        # Handle the FinergizeRecommenderAgent class
        if name == 'FinergizeRecommenderAgent':
            # Create a dynamic class that mimics the essential functionality
            class DynamicFinergizeRecommenderAgent:
                def __init__(self):
                    self.finergize_features = {}
                    self.question_templates = {}
                    self.chat_history = []
                    self.has_api = False
                    self.api_key = None
                
                def generate_survey(self, user_context):
                    # If we get here, the model will need to use fallback logic
                    return []
                
                def recommend_features(self, responses):
                    # If we get here, the model will need to use fallback logic
                    return {}
                    
            return DynamicFinergizeRecommenderAgent
        # For all other classes, use the default behavior
        return super().find_class(module, name)

class RecommenderService:
    """Service for feature recommendation operations"""
    
    def __init__(self):
        """Initialize the recommender service"""
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.openai_client = None
        self.load_model()
        
        # Configure OpenAI API key
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if openai_api_key:
            try:
                # Initialize the API client based on version
                if OPENAI_MODERN:
                    self.openai_client = OpenAI(api_key=openai_api_key)
                else:
                    openai.api_key = openai_api_key
                
                self.has_api = True
                self.logger.info("OpenAI API configured successfully")
                
                # Update the model with the API key if needed
                if self.model and hasattr(self.model, 'has_api'):
                    self.model.api_key = openai_api_key
                    self.model.has_api = True
                    self.logger.info("Injected OpenAI API key into model")
            except Exception as e:
                self.logger.error(f"Error configuring OpenAI API: {e}")
                self.has_api = False
        else:
            self.logger.warning("OpenAI API key not provided. Advanced features will be limited.")
            self.has_api = False
            
    def load_model(self):
        """Load the recommender model from joblib file"""
        try:
            # Get model path from environment or use default
            model_path = os.environ.get('MODEL_PATH', 'models/finergize_recommender_agent_clean.joblib')
            self.logger.info(f"Loading model from {model_path}")
            
            # Check if the file exists
            if not os.path.exists(model_path):
                self.logger.error(f"Model file not found at {model_path}")
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            try:
                # First try to load with standard joblib
                self.model = joblib.load(model_path)
            except (AttributeError, ImportError) as e:
                # If that fails, try with our custom unpickler
                self.logger.warning(f"Standard loading failed: {e}. Trying custom unpickler...")
                with open(model_path, 'rb') as f:
                    custom_unpickler = CustomUnpickler(f)
                    self.model = custom_unpickler.load()
                
            self.logger.info(f"Successfully loaded model from {model_path}")
            
            # Check if the model has OpenAI API key attribute
            if hasattr(self.model, 'has_api'):
                self.logger.info("Model has OpenAI integration capability")
                
                # Ensure the API key is not stored in the model
                if hasattr(self.model, 'api_key') and self.model.api_key:
                    self.logger.warning("Model contains an API key - this is not recommended")
                    # We'll inject a fresh key later in the __init__ method
                
            else:
                self.logger.warning("Model does not have OpenAI integration capability")
                
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            # Initialize a basic model with default configurations
            self.logger.info("Initializing with default configurations")
            self.initialize_default_model()
    
    def initialize_default_model(self):
        """Initialize a basic model if loading fails"""
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
        
        # Create a model-like object with the basic functionality needed
        class BasicModel:
            def __init__(self, features, templates, history, has_api, openai_key=None):
                self.finergize_features = features
                self.question_templates = templates
                self.chat_history = history
                self.has_api = has_api
                self.api_key = openai_key
                
            def generate_survey(self, user_context):
                """Simple implementation of survey generation"""
                questions = []
                
                # Core questions everyone gets
                questions.append(templates["financial_goals"])
                questions.append(templates["income_range"])
                questions.append(templates["financial_knowledge"])
                questions.append(templates["banking_habits"])
                questions.append(templates["savings_method"])
                questions.append(templates["loan_needs"])
                questions.append(templates["digital_comfort"])
                questions.append(templates["tracking_interest"])
                
                return questions
            
            def recommend_features(self, responses):
                """Simple implementation of feature recommendation"""
                # Create a basic recommendation
                features = []
                for feature_id, feature in self.finergize_features.items():
                    score = 5  # Default score
                    
                    # Adjust scores based on specific responses
                    if feature_id == "financial_education":
                        if responses.get("financial_knowledge") in ["beginner", "basic"]:
                            score += 3
                    
                    elif feature_id == "digital_banking":
                        if responses.get("digital_comfort") in ["very", "somewhat"]:
                            score += 2
                    
                    features.append({
                        "id": feature_id,
                        "name": feature["name"],
                        "score": score,
                        "explanation": feature["description"],
                        "tip": feature["ideal_for"]
                    })
                
                # Sort by score
                features.sort(key=lambda x: x["score"], reverse=True)
                
                return {
                    "prioritized_features": features,
                    "user_profile": {
                        "knowledge_level": responses.get("financial_knowledge", "beginner"),
                        "income_level": "Estimated from responses"
                    }
                }
        
        # Get OpenAI API key
        openai_api_key = os.environ.get('OPENAI_API_KEY')
                
        # Create our basic model
        features = self.finergize_features
        templates = self.question_templates
        history = self.chat_history
        self.model = BasicModel(features, templates, history, openai_api_key is not None, openai_api_key)
    
    def generate_survey(self, user_context):
        """Generate a personalized financial survey based on user context"""
        try:
            if self.model:
                questions = self.model.generate_survey(user_context)
                
                # If low literacy, enhance for accessibility
                if user_context.get('literacy_level') == 'low':
                    questions = self.enhance_for_accessibility(questions)
                    
                return questions
            else:
                self.logger.error("Model not initialized properly")
                return []
        except Exception as e:
            self.logger.error(f"Error generating survey: {e}")
            # Fall back to basic questions
            return list(self.question_templates.values())
    
    def enhance_for_accessibility(self, questions):
        """Add accessibility enhancements for users with lower literacy"""
        enhanced_questions = []
        
        for q in questions:
            enhanced_q = q.copy()
            
            # Add simplified language
            if "financial goals" in q["question"].lower():
                enhanced_q["simplified_question"] = "What do you want to do with your money?"
            elif "income" in q["question"].lower():
                enhanced_q["simplified_question"] = "How much money do you get each month?"
            elif "risk" in q["question"].lower():
                enhanced_q["simplified_question"] = "How okay are you if your money goes up and down?"
            elif "knowledge" in q["question"].lower():
                enhanced_q["simplified_question"] = "How much do you know about money?"
            elif "banking" in q["question"].lower():
                enhanced_q["simplified_question"] = "How do you use banks now?"
            elif "save" in q["question"].lower():
                enhanced_q["simplified_question"] = "How do you keep your savings?"
            elif "loan" in q["question"].lower():
                enhanced_q["simplified_question"] = "Do you need to borrow money?"
            elif "digital" in q["question"].lower():
                enhanced_q["simplified_question"] = "Do you use money apps on your phone?"
            elif "tracking" in q["question"].lower():
                enhanced_q["simplified_question"] = "Do you want to see where your money goes?"
            else:
                # Simplify version for other questions
                enhanced_q["simplified_question"] = q["question"].replace("financial", "money").replace("investment", "saving money")
            
            # Add help text
            enhanced_q["help_text"] = self.generate_help_text(q)
            
            # Add visual indicators for options
            if enhanced_q.get("options"):
                for option in enhanced_q["options"]:
                    option["icon"] = self.assign_option_icon(option["text"])
            
            enhanced_questions.append(enhanced_q)
        
        return enhanced_questions
    
    def generate_help_text(self, question):
        """Generate helpful text for questions"""
        question_text = question["question"].lower()
        
        if "financial goals" in question_text:
            return "These are things you want to do with your money in the future."
        elif "income" in question_text:
            return "This is how much money you get each month from your job or business."
        elif "risk" in question_text:
            return "Lower risk means your money is safer but grows slower. Higher risk means it might grow faster but could also lose value."
        elif "knowledge" in question_text:
            return "How much you know about money and financial matters."
        elif "banking habits" in question_text:
            return "How you currently use banking services for your money needs."
        elif "save money" in question_text:
            return "Different ways to keep your savings safe and growing."
        elif "loan" in question_text:
            return "Whether you need to borrow money for personal or business needs."
        elif "digital" in question_text:
            return "How comfortable you are using apps on your phone for money management."
        elif "tracking" in question_text:
            return "Understanding where your money goes each month."
        else:
            return "Please select the option that best describes your situation."
    
    def assign_option_icon(self, option_text):
        """Assign a simple icon to an option"""
        option_text = option_text.lower()
        
        if "save" in option_text or "emergency" in option_text or "bank" in option_text:
            return "💰"
        elif "invest" in option_text or "growth" in option_text or "mutual" in option_text:
            return "📈"
        elif "loan" in option_text or "borrow" in option_text:
            return "🏦"
        elif "education" in option_text or "learn" in option_text:
            return "📚"
        elif "retirement" in option_text:
            return "🌴"
        elif "community" in option_text or "chit" in option_text or "group" in option_text:
            return "👨‍👩‍👧‍👦"
        elif "track" in option_text or "analytics" in option_text or "spending" in option_text:
            return "📊"
        elif "digital" in option_text or "mobile" in option_text or "app" in option_text:
            return "📱"
        elif "conservative" in option_text or "low" in option_text:
            return "🛡️"
        elif "aggressive" in option_text or "high" in option_text:
            return "🚀"
        else:
            return "✅"
    
    def recommend_features(self, responses):
        """
        Process survey responses and generate prioritized feature recommendations
        for the six Finergize features
        """
        try:
            if self.model:
                # Log the responses for debugging
                self.logger.info(f"Processing recommendations for responses: {json.dumps(responses)}")
                
                # Check if OpenAI integration is enabled and configured
                if hasattr(self.model, 'has_api') and self.model.has_api and self.model.api_key:
                    self.logger.info("Using OpenAI-enhanced recommendations")
                    
                    try:
                        # Prepare a prompt for OpenAI
                        prompt = f"""
                        Based on the following survey responses, recommend and prioritize the six Finergize features for this user:

                        Survey Responses:
                        {json.dumps(responses, indent=2)}
                        
                        Finergize Features:
                        1. Digital Banking - Modern mobile banking services with UPI, bill payments, and account management
                        2. Mutual Funds - Simple investment options in diversified mutual funds
                        3. Community Savings - Group-based savings programs for family/community goals
                        4. Micro Loans - Small, accessible loans with simple application process
                        5. Analytics Profile - Personal financial insights and spending analysis
                        6. Financial Education - Courses and resources on financial literacy
                        
                        For each feature, provide:
                        1. A relevance score from 1-10 (10 being most relevant)
                        2. A brief explanation of why it's recommended based on their responses
                        3. A personalized tip for getting started with the feature
                        
                        Order the features from most to least relevant for this specific user.
                        Format your response as JSON with each feature as a key, containing score, explanation and tip fields.
                        """
                        
                        # Use the appropriate OpenAI client based on what's available
                        if OPENAI_MODERN and self.openai_client:
                            # Use the modern client (v1.0+)
                            response = self.openai_client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "system", "content": "You are a specialized financial advisor for Finergize, an Indian financial platform."},
                                    {"role": "user", "content": prompt}
                                ],
                                temperature=0.7,
                                response_format={"type": "json_object"}
                            )
                            ai_response = response.choices[0].message.content
                        else:
                            # Fall back to the old client if necessary
                            response = openai.ChatCompletion.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "system", "content": "You are a specialized financial advisor for Finergize, an Indian financial platform."},
                                    {"role": "user", "content": prompt}
                                ],
                                temperature=0.7,
                                response_format={"type": "json_object"}
                            )
                            ai_response = response.choices[0].message.content
                        
                        # Extract and parse the response
                        try:
                            recommendations = json.loads(ai_response)
                            
                            # Format for display
                            formatted_recommendations = {
                                "prioritized_features": [],
                                "user_profile": {
                                    "knowledge_level": responses.get("financial_knowledge", "beginner"),
                                    "income_level": self.map_income_level(responses.get("income_range", "income_medium"))
                                }
                            }
                            
                            # Add features in order of relevance
                            for feature_id, details in sorted(recommendations.items(), key=lambda x: x[1].get('score', 0), reverse=True):
                                feature_name = self.get_feature_name(feature_id)
                                
                                formatted_recommendations["prioritized_features"].append({
                                    "id": feature_id,
                                    "name": feature_name,
                                    "score": details.get('score', 5),
                                    "explanation": details.get('explanation', ''),
                                    "tip": details.get('tip', '')
                                })
                            
                            return formatted_recommendations
                        
                        except json.JSONDecodeError:
                            self.logger.error("Error parsing OpenAI response as JSON")
                            self.logger.error(f"Raw response: {ai_response}")
                            # Continue to fallback if JSON parsing fails
                        
                    except Exception as e:
                        self.logger.error(f"Error using OpenAI: {e}")
                        # Continue to use base algorithm or fallback
                
                # If OpenAI integration failed or is not available, use base algorithm
                self.logger.info("Using base recommendation algorithm")
                return self.model.recommend_features(responses)
            else:
                self.logger.error("Model not initialized properly")
                return self.generate_fallback_recommendations(responses)
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return self.generate_fallback_recommendations(responses)
    
    def get_features(self):
        """Get all available Finergize features"""
        try:
            features = {}
            
            # Use model features if available
            if hasattr(self.model, 'finergize_features'):
                features = self.model.finergize_features
            # Fall back to our basic features
            elif hasattr(self, 'finergize_features'):
                features = self.finergize_features
            
            return features
        except Exception as e:
            self.logger.error(f"Error retrieving features: {e}")
            return {}
    
    def get_feature_name(self, feature_id):
        """Get the display name for a feature ID"""
        # Clean up the feature ID if needed
        feature_id = feature_id.lower().strip().replace(" ", "_")
        
        # Get features from model or fallback
        features = self.get_features()
        
        # Check for exact matches first
        if feature_id in features:
            return features[feature_id]["name"]
        
        # Try partial matches
        for key, feature in features.items():
            if key in feature_id or feature_id in key:
                return feature["name"]
            if feature["name"].lower() in feature_id or feature_id in feature["name"].lower():
                return feature["name"]
        
        # Return a default if no match found
        return feature_id.replace("_", " ").title()
    
    def generate_fallback_recommendations(self, responses):
        """Generate basic feature recommendations as a fallback"""
        # Define the Finergize features if not available from model
        if not hasattr(self, 'finergize_features'):
            self.finergize_features = {
                "digital_banking": {
                    "name": "Digital Banking",
                    "description": "Secure digital banking services with UPI payments",
                    "ideal_for": "Users looking for convenient, modern banking"
                },
                "mutual_funds": {
                    "name": "Mutual Funds",
                    "description": "Simple investments in diversified mutual funds",
                    "ideal_for": "Users interested in growing wealth through investments"
                },
                "community_savings": {
                    "name": "Community Savings",
                    "description": "Group savings programs for community members",
                    "ideal_for": "Users who want to save with friends and family"
                },
                "micro_loans": {
                    "name": "Micro Loans",
                    "description": "Small, accessible loans with simple application",
                    "ideal_for": "Users needing small amounts of credit"
                },
                "analytics_profile": {
                    "name": "Analytics Profile",
                    "description": "Personalized financial insights and spending analysis",
                    "ideal_for": "Users who want to understand spending patterns"
                },
                "financial_education": {
                    "name": "Financial Education",
                    "description": "Courses and articles on financial literacy",
                    "ideal_for": "Users looking to improve financial knowledge"
                }
            }
        
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