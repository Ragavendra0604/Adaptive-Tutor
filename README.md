# Adaptive DSA Tutor

An intelligent, adaptive learning platform designed to teach Data Structures and Algorithms (DSA). This application combines **Spaced Repetition (SM-2)**, **Retrieval-Augmented Generation (RAG)**, and **Real-time Code Execution** to provide a personalized learning experience.

## 🚀 Features

* **Adaptive Learning Path:** Uses the **SM-2 algorithm** (SuperMemo-2) to track your "Mastery" of concepts (e.g., Binary Search, DP). It calculates concept strength, easiness factors, and optimal review intervals to ensure efficient learning.
* **Interactive Code Practice:**
    * **Built-in Code Editor:** A robust editor supporting Python (extensible to C++/Java) with syntax highlighting.
    * **Real-time Execution:** Integrates with **Judge0** API to compile and run code securely.
    * **Automated Grading:** Runs code against hidden test cases and uses LLM verification for logic, style, and edge-case handling.
* **AI Chat Tutor:**
    * **RAG-Powered Assistant:** Context-aware chatbot that retrieves relevant information from a vector database (FAISS) populated with high-quality DSA resources.
    * **Hallucination Resistant:** Uses strict system prompts to ensure answers are grounded in retrieved context.
    * **Streaming Responses:** Provides a natural, real-time conversational flow using WebSockets.
* **Detailed Feedback:** After submission, users receive line-by-line feedback, performance metrics (runtime/memory), and actionable style suggestions.
* **Visual Progress Tracking:** Users can view their mastery levels via dynamic progress bars.

---

## 🛠️ Tech Stack

### Backend
* **Framework:** Python (FastAPI)
* **Database:** MongoDB (User data, Question Bank, Chat Logs)
* **Vector Store:** FAISS (Facebook AI Similarity Search)
* **AI/LLM:** OpenRouter API
* **Code Sandbox:** Judge0 CE (via RapidAPI)

### Frontend
* **Framework:** React (Vite)
* **Styling:** CSS Modules / Inline Styles (Dark Mode Theme)
* **Components:** Custom `TestResultViewer` for LeetCode-style submission feedback.

---

## ⚙️ Prerequisites

Before you begin, ensure you have the following installed:
* **Python 3.11+**
* **Node.js & npm** (v18+ recommended)
* **MongoDB** (Running locally on default port `27017` or provide a cloud URI)

### Required API Keys
1.  **[OpenRouter Key](https://openrouter.ai/):** For the AI Tutor and Grading.
2.  **[RapidAPI Key for Judge0](https://rapidapi.com/judge0-official/api/judge0-ce):** For code compilation.

---

## 📦 Installation & Setup

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd Adaptive_Tutor
````

### 2\. Backend Setup

Navigate to the backend folder, create a virtual environment, and install dependencies.

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3\. Configuration (.env)

Create a `.env` file in the **root** of your project (parent of `backend/`) containing your API keys:

```env
# Database
MONGO_URI=mongodb://localhost:27017
MONGO_DB=adaptive_tutor

# AI / LLM (OpenRouter)
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=gpt-4o-mini
OPENROUTER_API_URL=[https://openrouter.ai/api/v1/chat/completions](https://openrouter.ai/api/v1/chat/completions)

# Code Execution (Judge0 via RapidAPI)
JUDGE0_API_URL=[https://judge0-ce.p.rapidapi.com](https://judge0-ce.p.rapidapi.com)
JUDGE0_API_HOST=judge0-ce.p.rapidapi.com
JUDGE0_API_KEY=your-rapidapi-key-here

# Vector Store
EMBEDDING_MODEL=all-MiniLM-L6-v2
FAISS_INDEX_PATH=faiss_index
```

### 4\. Seed the Database

Populate the question bank with initial DSA problems.

```bash
# Ensure you are in the root directory and venv is active
python backend/scripts/seed_question_bank_massive.py
python backend/scripts/seed_binary_search.py
```

### 5\. Run the Backend Server

```bash
# Run from the root directory
python -m uvicorn backend.app.main:app --reload
```

> The Backend API will start at `http://localhost:8000`

### 6\. Frontend Setup

Open a **new terminal**, navigate to the frontend folder, and start the UI.

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

> The Frontend will start at `http://localhost:5173`

-----

## 🖥️ Usage Guide

### 1\. Login

Navigate to the Practice page. Enter a **User ID** (e.g., `student1`). If the user doesn't exist, the system automatically creates a profile.

### 2\. Practice Concepts

  * Use the **Concept Dropdown** to select a topic (e.g., `binary_search`, `bubble_sort`).
  * Click **"Get Questions"**. The system will fetch questions suited to your current mastery level.
  * **Code Questions:** Write Python code in the editor to solve the problem.
  * **Submit:** Click "Submit Answer". The system runs your code against test cases and provides immediate feedback.

### 3\. Review Feedback

  * View the **Result Viewer** to see which test cases passed/failed.
  * Read the **AI Feedback** for code quality improvements.
  * Check your updated **Mastery Score** to see your progress.

### 4\. AI Chat

  * Switch to the **Chat** tab.
  * Ask conceptual questions like *"How does Quicksort handle pivot selection?"*.
  * The bot will retrieve accurate context and stream the answer.

-----

## 📂 Project Structure

```text
Adaptive_Tutor/
├── backend/
│   ├── app/
│   │   ├── api/            # API Routes (practice, submit, stream)
│   │   ├── core/           # Config & Settings
│   │   ├── db/             # MongoDB connection
│   │   ├── adaptive/       # Spaced Repetition Logic (SM-2)
│   │   ├── code/           # Judge0 Client & Execution
│   │   ├── rag/            # RAG Engine & Vector Retrieval
│   │   ├── rubrics/        # LLM Grading Prompts
│   │   └── scraper/        # Web scraper for knowledge base
│   ├── scripts/            # DB Seeding Scripts
│   └── requirements.txt    # Dependencies
├── frontend/
│   ├── src/
│   │   ├── components/     # UI Components (TestResultViewer)
│   │   ├── pages/          # PracticePage, ChatPage
│   │   └── api.js          # API Fetch wrappers
│   └── package.json        # Dependencies
└── README.md
```
