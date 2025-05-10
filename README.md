# Finergize Recommender API with OpenAI Integration

This is the backend API service for the Finergize Financial Feature Recommender system with OpenAI integration. It provides personalized survey generation and feature recommendations for financial app users in India.

## Features

- OpenAI-enhanced personalization for both survey questions and feature recommendations
- Survey generation API that produces tailored questions based on user context
- Feature recommendation API that prioritizes financial features based on survey responses
- Support for multiple literacy levels and accessibility enhancements
- Production-ready deployment configuration for Render

## API Endpoints

### 1. Get Survey Questions

```
GET /api/survey
```

**Query Parameters:**
- `location` - User's location in India (e.g., "Delhi NCR", "Mumbai")
- `age` - User's age group (e.g., "25-34", "35-44")
- `interest` - Primary financial interest (e.g., "Investing", "Saving")
- `literacy_level` - Level of financial literacy (e.g., "moderate", "low")

**Response:**
```json
{
  "success": true,
  "survey": [
    {
      "id": "financial_goals",
      "question": "What are your primary financial goals?",
      "type": "multiple-choice",
      "options": [
        {"id": "save", "text": "Save for emergencies"},
        {"id": "invest", "text": "Invest for long-term growth"},
        ...
      ],
      "allowMultiple": true
    },
    ...
  ]
}
```

### 2. Get Feature Recommendations

```
POST /api/recommend
```

**Request Body:**
```json
{
  "responses": {
    "financial_goals": ["save", "invest"],
    "income_range": "income_medium",
    "financial_knowledge": "beginner",
    "banking_habits": "mobile",
    ...
  }
}
```

**Response:**
```json
{
  "success": true,
  "recommendations": {
    "prioritized_features": [
      {
        "id": "financial_education",
        "name": "Financial Education",
        "score": 9,
        "explanation": "Learn essential financial skills through courses and articles.",
        "tip": "Start with the basic modules on budgeting and saving."
      },
      ...
    ],
    "user_profile": {
      "knowledge_level": "beginner",
      "income_level": "₹30,000 - ₹60,000"
    }
  }
}
```

### 3. Get All Features

```
GET /api/features
```

**Response:**
```json
{
  "success": true,
  "features": {
    "digital_banking": {
      "name": "Digital Banking",
      "description": "Secure digital banking services with UPI payments, bill payments, and account management",
      "ideal_for": "Users looking for convenient, modern banking with minimal fees"
    },
    ...
  }
}
```

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- pip for package management
- OpenAI API key

### Local Development

1. Clone the repository:
```
git clone https://github.com/yourusername/finergize-api.git
cd finergize-api
```

2. Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Create a `.env` file for environment variables:
```
SECRET_KEY=your_secret_key_here
OPENAI_API_KEY=your_openai_api_key  # Required for enhanced recommendations
USE_OPENAI=True
DEBUG=True
```

5. Place your model file in the models directory:
```
mkdir -p models
# Copy your finergize_recommender_agent.joblib to the models directory
```

6. Run the application:
```
python app.py
```

The API will be available at `http://localhost:8080`.

## Deployment to Render

This repository is configured for easy deployment on Render with OpenAI integration.

### Steps to Deploy

1. Create a new Web Service on Render
2. Connect your GitHub/GitLab repository
3. Use the following settings:
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
4. Add the following environment variables:
   - `SECRET_KEY`: A secure random string
   - `OPENAI_API_KEY`: Your OpenAI API key (required for enhanced recommendations)
   - `USE_OPENAI`: "True"
   - `MODEL_PATH`: "models/finergize_recommender_agent.joblib"
   - `PORT`: 8080
   - `PYTHON_VERSION`: 3.10.11
5. Make sure to upload your model file to the Render service:
   - You can do this by including the model file in your repository
   - Or, you can upload it via Render's shell/environment

### Important Notes About OpenAI Integration

1. The OpenAI API key is required for the enhanced personalization features
2. Ensure your API key has sufficient quota for production usage
3. The system will fallback to basic rule-based recommendations if OpenAI API calls fail
4. Monitor your OpenAI API usage to avoid unexpected costs

### Connecting Your Next.js Frontend

For your Next.js TypeScript frontend:

1. Add the Render API endpoint URL to your environment variables
2. Create API service functions for fetching survey questions and submitting responses
3. Implement the user interface using the API responses

## Model Information

The recommendation system uses a joblib-serialized model with OpenAI integration that prioritizes six key Finergize features:

1. Digital Banking - Modern mobile banking services with UPI and bill payments
2. Mutual Funds - Simple investment options in diversified mutual funds
3. Community Savings - Group-based savings programs for family/community
4. Micro Loans - Small, accessible loans with simple application process
5. Analytics Profile - Personal financial insights and spending analysis
6. Financial Education - Courses and resources on financial literacy

The OpenAI integration enhances:
- Survey generation with additional personalized questions
- Feature recommendations with more detailed and contextual explanations
- Customized getting-started tips based on user responses

## License

[MIT License](LICENSE)