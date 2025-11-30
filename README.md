# Winning The Fight Against Medical Debt

> **AI-Powered Medical Bill Analysis with Persistent Sessions**  
> Automated extraction, validation, and explanation of medical bills using Google's Gemini AI with session-based follow-up questions.

---

## 🚀 Features

### Core Functionality
- ✅ **Automated Bill Extraction** - Extracts data from PDF medical bills
- ✅ **Charge Analysis** - Identifies and structures all charges with CPT codes
- ✅ **Duplicate Detection** - Finds duplicate charges automatically
- ✅ **Code Validation** - Validates CPT codes and identifies deprecated/incorrect codes
- ✅ **Plain English Explanations** - Translates medical jargon into patient-friendly language
- ✅ **Parallel Processing** - Runs multiple auditors simultaneously for efficiency

### Advanced Features
- 🔄 **Persistent Sessions** - DatabaseSessionService with SQLite storage
- 💬 **Interactive Q&A** - Ask follow-up questions about bill analysis
- 🧠 **Context Memory** - Chatbot remembers entire conversation history
- 📊 **Session Sharing** - Multiple agents share the same session context
- ⚡ **Events Compaction** - Efficient memory management for long conversations
- 📝 **Comprehensive Logging** - Detailed execution logs with timestamps

---

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)

---

## 🛠️ Installation

### Prerequisites

- **Python 3.8+**
- **Google API Key** (Gemini AI)
- **Poppler** (for PDF processing)

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd Capstoneproject
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
cd src
pip install -r requirements.txt
```

### Step 4: Set Environment Variables

```bash
# Windows PowerShell
$env:GOOGLE_API_KEY = "your-google-api-key-here"
$env:POPPLER_BIN_PATH = "C:\path\to\poppler\bin"

# Linux/Mac
export GOOGLE_API_KEY="your-google-api-key-here"
export POPPLER_BIN_PATH="/path/to/poppler/bin"
```

### Step 5: Verify Installation

```bash
python tests/run_tests.py
```

---

## ⚡ Quick Start

### Process a Medical Bill

```python
from orchestrator import MedicalBillOrchestrator
from pathlib import Path

# Initialize orchestrator
orchestrator = MedicalBillOrchestrator()

# Process bill
bill_file = Path("bills/dummy_bill.pdf")
results = await orchestrator.process_bill(bill_file)

print(f"Status: {results['status']}")
print(f"Findings: {results['final_output']}")
```

### Run Complete Workflow with Follow-up Questions

```bash
cd src
python main.py
```

**What happens:**
1. Processes medical bill (extraction, analysis, auditing)
2. Shows results
3. Initializes chatbot with session memory
4. Asks 3 pre-programmed follow-up questions
5. Enters interactive mode for your questions

### Interactive Mode Example

```
👤 Your question: What was the total charge?
🤖 Bot: The total charge was $450, consisting of...

👤 Your question: Were any duplicates found?
🤖 Bot: No duplicate charges were detected...

👤 Your question: quit
👋 Goodbye!
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | ✅ Yes | None | Your Google Gemini API key |
| `POPPLER_BIN_PATH` | ❌ No | Auto-detect | Path to Poppler binaries |
| `DATABASE_URL` | ❌ No | `sqlite+aiosqlite:///medical_bill_agent_data.db` | Database connection string |


---


---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Main Application                         │
│                       (main.py)                              │
└───────────────────┬─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌──────────────────┐   ┌──────────────────────┐
│ Bill Processing  │   │ Interactive Q&A      │
│ (Orchestrator)   │   │ (Session Chatbot)    │
└────────┬─────────┘   └──────────┬───────────┘
         │                        │
         ▼                        ▼
┌─────────────────────────────────────────┐
│       Shared Session (Database)         │
│   "bill-analysis-session"               │
└─────────────────────────────────────────┘
```

### Agent Workflow

```
Bill PDF
   │
   ▼
┌──────────────────────┐
│ BillExtractionAgent  │ → Extracts raw text/JSON
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ ChargeExtractionAgent│ → Structures charges & CPT codes
└──────────┬───────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│      Parallel Processing (3 agents)     │
├──────────────────┬──────────────────────┤
│ DuplicateAuditor │ WrongCodesAuditor    │
│                  │ ChargeExplainer       │
└──────────────────┴──────────────────────┘
           │
           ▼
┌──────────────────────┐
│  GoverningAgent      │ → Tracks execution & reports
└──────────────────────┘
```

### Session Flow

```
1. Process Bill → Results
2. Summary Agent → Writes to Shared Session
3. Chatbot Agent → Reads from Shared Session
4. User Questions → Chatbot responds with context
5. Compaction → Efficient memory management
```

---





