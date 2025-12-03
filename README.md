# Winning The Fight Against Medical Debt

> **AI-Powered Medical Bill Analysis with Persistent Sessions**  
> Automated extraction, validation, and explanation of medical bills using Google's Gemini AI with session-based follow-up questions.

---

## 🚀 Features

### Core Functionality
- ✅ **Automated Bill Extraction** - Extracts data from PDF medical bills using text extraction
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
- ⚡ **Events Compaction** - Efficient memory management for long conversations (every 3 invocations)
- 📝 **Comprehensive Logging** - Detailed execution logs with timestamps
- 🔁 **Retry Logic** - Automatic retry with exponential backoff for API calls

---

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Project Structure](#project-structure)


---

## 🛠️ Installation

### Prerequisites

- **Python 3.8+** (Python 3.13+ recommended)
- **Google API Key** (Gemini AI) - [Get one here](https://aistudio.google.com/app/apikey)
- **Poppler** (for PDF processing) - [Download here](https://github.com/oschwartz10612/poppler-windows/releases/)

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd WinningFightAgainstMedicalDebt-main
```

### Step 2: Create Virtual Environment

```bash
# Windows PowerShell
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

**Dependencies installed:**
- `google-adk` - Google Agent Development Kit
- `reportlab` - PDF generation
- `pdf2image` - PDF to image conversion
- `pillow` - Image processing
- `PyMuPDF` - PDF text extraction
- `sqlalchemy` - Database ORM
- `aiosqlite` - Async SQLite support

### Step 4: Set Environment Variables

**Windows PowerShell:**
```powershell
$env:GOOGLE_API_KEY = "your-google-api-key-here"
$env:POPPLER_BIN_PATH = "C:\path\to\poppler\bin"  # Optional if auto-detect fails
```

**Linux/Mac:**
```bash
export GOOGLE_API_KEY="your-google-api-key-here"
export POPPLER_BIN_PATH="/path/to/poppler/bin"  # Optional
```

**To make permanent (Windows):**
```powershell
[Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", "your-key-here", "User")
```

### Step 5: Add Medical Bills

Place your PDF medical bills in the `src/bills/` directory:
```
src/bills/
├── dummy_bill.pdf       # Sample bill included
├── Sample_bill.pdf      # Sample bill included
└── your_bill.pdf        # Add your bills here
```

### Step 6: Verify Installation

```bash
cd src
python tests/run_tests.py
```

---

## ⚡ Quick Start

### 1. Run the Complete Application

```bash
cd src
python main.py
```

**What happens:**
1. 📄 **Bill Processing Stage:**
   - Extracts bill data from PDF
   - Identifies all charges and CPT codes
   - Runs parallel audits (duplicates, code validation)
   - Generates explanations in plain English
   - Writes results to shared database session

2. 💬 **Interactive Q&A Stage:**
   - Chatbot initializes with session context
   - Asks 3 pre-programmed follow-up questions
   - Enters interactive mode for your custom questions

3. 🎯 **Session Context:**
   - All agents share the same session ID: `bill-analysis-session`
   - Chatbot has full context of bill analysis
   - Ask any questions about charges, codes, or totals

### 2. Interactive Mode Example

```
INTERACTIVE MODE
You can now ask follow-up questions about the bill.
The chatbot has access to ALL bill analysis results from the shared session!
Type 'quit' or 'exit' to end the session.

👤 Your question: What was the total charge?
🤖 gemini-2.5-flash-lite > The total charge was $450, consisting of an office visit ($150) and lab work ($300).

👤 Your question: Were any duplicate charges found?
🤖 gemini-2.5-flash-lite > No duplicate charges were detected in the bill analysis.

👤 Your question: Are the CPT codes valid?
🤖 gemini-2.5-flash-lite > Yes, all CPT codes are valid and current.

👤 Your question: quit
👋 Goodbye!
```

### 3. Programmatic Usage (Custom Integration)

```python
import asyncio
from orchestrator import MedicalBillOrchestrator
from pathlib import Path

async def analyze_bill():
    # Initialize orchestrator
    orchestrator = MedicalBillOrchestrator()
    
    # Process bill
    bill_file = Path("bills/your_bill.pdf")
    results = await orchestrator.process_bill(bill_file)
    
    # Access results
    print(f"Status: {results['status']}")
    print(f"Total Stages: {len(results['stages'])}")
    print(f"\nFinal Analysis:\n{results['final_output']}")
    
    # Access specific stage data
    charge_data = results['stages']['charge_extraction']['data']
    audit_results = results['stages']['parallel_analysis']['data']

# Run
asyncio.run(analyze_bill())
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | ✅ Yes | None | Your Google Gemini API key |
| `POPPLER_BIN_PATH` | ❌ No | Auto-detect | Path to Poppler binaries (required for PDF conversion) |
| `DATABASE_URL` | ❌ No | `sqlite+aiosqlite:///medical_bill_agent_data.db` | Database connection string for session storage |

### Application Settings

The following settings are configured in `src/utils/config.py`:

```python
DEFAULT_MODEL = "gemini-2.5-flash-lite"  # Gemini model to use
TEMPERATURE = 0.1                        # LLM temperature (lower = more deterministic)
COMPACTION_INTERVAL = 3                  # Compact session every 3 invocations
OVERLAP_SIZE = 1                         # Keep 1 previous turn for context
APP_NAME = "medical_bill_processing"     # Application name for session service
```

### Model Configuration

The application uses **Gemini 2.5 Flash Lite** with the following retry configuration:
- **Attempts:** 5 retries
- **Exponential Backoff:** Base 2, Initial delay 1 second
- **Retry on HTTP Status:** 429 (Rate Limit), 500, 503, 504 (Server Errors)

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
5. Compaction → Efficient memory management (every 3 invocations)
```

### Key Design Patterns

- **Orchestrator Pattern**: `MedicalBillOrchestrator` coordinates all agents
- **Agent Wrapper Pattern**: Unified interface for all specialized agents
- **Shared Session Pattern**: Multiple agents share the same conversation context
- **Async/Await**: All operations are asynchronous for better performance

---

## 📁 Project Structure

```
WinningFightAgainstMedicalDebt-main/
├── README.md                          
└── src/
    ├── main.py                        # Main entry point
    ├── requirements.txt               # Python dependencies
    ├── medical_bill_agent_data.db     # SQLite database (created on first run)
    │
    ├── agents/                        # Specialized AI agents
    │   ├── __init__.py
    │   ├── bill_extraction.py         # PDF text extraction agent
    │   ├── charge_extraction.py       # Charge & CPT code extraction
    │   ├── duplicate_auditor.py       # Duplicate charge detection
    │   ├── wrong_codes_auditor.py     # CPT code validation
    │   ├── charge_explainer.py        # Plain English explanations
    │   └── governing_agent.py         # Execution tracking & reporting
    │
    ├── orchestrator/                  # Workflow coordination
    │   ├── __init__.py
    │   ├── medical_bill_orchestrator.py   # Main orchestrator
    │   ├── agent_wrapper.py           # Agent execution wrapper
    │   
    │
    ├── schemas/                       # Data structures
    │   ├── __init__.py
    │   └── bill_schema.py             # Bill data models
    │
    ├── utils/                         # Utilities
    │   ├── __init__.py
    │   ├── config.py                  # Configuration management
    │   └── image_utils.py             # PDF/Image processing
    │
    ├── observability/                 # Logging & monitoring
    │   ├── __init__.py
    │   └── logger.py                  # Custom logger setup
    │
    ├── bills/                         # Input PDFs
    │   ├── dummy_bill.pdf             # Sample bill 1
    │   └── Sample_bill.pdf            # Sample bill 2
    │
    ├── logs/                          # Application logs
    │   └── medical_bill_YYYYMMDD_HHMMSS.log
    │
    └── tests/                         # Test suite
        ├── __init__.py
        ├── run_tests.py               # Test runner
        ├── test_integration.py        # Integration tests
        └── test_main.py               # Unit tests
```

### Improvements Continued.. / Continous Learning:
-   Use Model Context Protocol and Evaluation
-   Deploy the Agents - to learn further steps in the end-to-end phase
-   Organize prompts in separate folder for better managing
-   Implement Web Interface with file uploader to give better UX
-   Externalize all configurable parameters outside the design/solution
-   Implement solution to perform a check to use the existing local persistent caching to reduce cost of using LLM for similar inputs in future
-   Define DoD, continuously and systematically improvise Agent quality and maturity



---







