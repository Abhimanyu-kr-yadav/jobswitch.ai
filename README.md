# JobSwitch.ai 🚀  
*An AI-powered Career Copilot Platform*  

JobSwitch.ai is a comprehensive **AI-driven career assistant** that helps users discover jobs, optimize resumes, prepare for interviews, grow their network, and plan long-term career strategies. It leverages **Agentic AI** with IBM **watsonx.ai** and **watsonx Orchestrate** to provide **personalized, end-to-end career support**.  

---

## ✨ Features
- 🔍 **Job Discovery Agent** – Recommends jobs from LinkedIn, Indeed, Glassdoor, AngelList, and company APIs.  
- 🧑‍💻 **Skills Analysis Agent** – Detects skill gaps and generates personalized learning paths.  
- 📄 **Resume Optimization Agent** – Optimizes resumes for ATS compatibility and job-specific tailoring.  
- 🎤 **Interview Preparation Agent** – Conducts mock interviews with AI-powered real-time feedback.  
- 🤝 **Networking Agent** – Generates outreach campaigns and manages professional contacts.  
- 📈 **Career Strategy Agent** – Builds long-term personalized career roadmaps.  

---

## 🏗️ Architecture
- **Frontend**: React.js (UI Dashboard, Components, State Management)  
- **Backend**: FastAPI (REST API Gateway, Authentication, Orchestration)  
- **AI Orchestration**: IBM WatsonX Orchestrate + LangChain  
- **AI Models**: IBM watsonx.ai (NLP, embeddings, LLMs)  
- **Databases**: PostgreSQL / SQLServer, Redis (cache)  
- **Integrations**: LinkedIn API, Indeed API, Glassdoor API, AngelList API  
- **Cloud**: IBM Cloud, Azure, AWS  

---

## 📦 Tech Stack
- **Frontend**: React, Bootstrap, Axios, Redux/Context API  
- **Backend**: FastAPI, Python, SQLAlchemy  
- **Database**: PostgreSQL, Redis Cache  
- **DevOps**: Docker, Kubernetes, GitHub Actions / Jenkins (CI/CD)  
- **Cloud AI**: IBM watsonx.ai, Watson Orchestrate, LangChain  

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Abhimanyu-kr-yadav/jobswitch.ai.git
cd jobswitch.ai
```


### 2️⃣ Backend Setup (FastAPI)
```bash
cd backend-server
```

## Create & Activate Virtual Environment
### Windows PowerShell
```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / MacOS
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Install Dependencies
```bash
pip install -r requirements.txt
```

## Environment Variables

### Create a .env file inside backend-server/:
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/jobswitch
REDIS_URL=redis://localhost:6379/0
WATSONX_API_KEY=your_watsonx_api_key
JWT_SECRET=your_secret_key
```

## Run the Server
```bash
uvicorn main:app --reload
```


### By default the API runs at 👉 http://127.0.0.1:8000

### Swagger Docs 👉 http://127.0.0.1:8000/docs



### 3️⃣ Frontend Setup (React)
```bash
cd ../jobswitch-ui
```

## Install Dependencies
```bash
npm install
```

## Environment Variables
### Create .env file inside jobswitch-ui/:
```bash
REACT_APP_API_URL=http://127.0.0.1:8000/api/v1
```

## Start React App
```bash
npm start
```

### Frontend runs at 👉 http://localhost:3000
