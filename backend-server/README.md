# JobSwitch.ai Backend Server

Enhanced FastAPI backend with AI agent orchestration for the JobSwitch.ai career copilot platform.

## Features

- **AI Agent Orchestration**: Coordinate multiple specialized AI agents using WatsonX Orchestrate
- **WatsonX.ai Integration**: Advanced AI capabilities for job matching, resume optimization, and career advice
- **LangChain Framework**: Structured AI workflows and conversation management  
- **Database Models**: Comprehensive data models for users, jobs, and agent interactions
- **Scalable Architecture**: Modular design supporting multiple AI agents and external integrations

## Project Structure

```
backend-server/
├── app/
│   ├── agents/          # AI agent implementations
│   │   └── base.py      # Base agent interface
│   ├── api/             # API routes and endpoints
│   ├── core/            # Core application components
│   │   ├── config.py    # Configuration management
│   │   ├── database.py  # Database setup and utilities
│   │   └── orchestrator.py # Agent orchestration framework
│   ├── integrations/    # External service integrations
│   │   ├── watsonx.py   # WatsonX.ai client
│   │   └── langchain_utils.py # LangChain utilities
│   ├── models/          # Database models
│   │   ├── user.py      # User profile models
│   │   ├── job.py       # Job and career models
│   │   └── agent.py     # Agent data models
│   └── main.py          # Main application file
├── requirements.txt     # Python dependencies
├── .env.example        # Environment configuration template
├── run.py              # Application runner
└── main.py             # Legacy compatibility file
```

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration values
   ```

3. **Run the Application**:
   ```bash
   python run.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn app.main:app --reload
   ```

## Configuration

Key environment variables:

- `WATSONX_API_KEY`: Your WatsonX.ai API key
- `WATSONX_PROJECT_ID`: Your WatsonX.ai project ID
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT secret key (change in production)

## API Endpoints

- `GET /health` - Health check and system status
- `POST /api/generate-cover-letter` - Legacy cover letter generation
- `GET /` - Application information

Additional agent-specific endpoints will be added as agents are implemented.

## Development

The application uses:
- **FastAPI** for the web framework
- **SQLAlchemy** for database ORM
- **Pydantic** for data validation
- **WatsonX.ai** for AI capabilities
- **LangChain** for AI workflow management

## Next Steps

This foundation supports the implementation of specialized AI agents:
- Job Discovery Agent
- Skills Analysis Agent  
- Resume Optimization Agent
- Interview Preparation Agent
- Networking Agent
- Career Strategy Agent