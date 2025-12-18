# Config-Copilot - Intent-Driven Oracle ERP Configuration Agent

An AI-powered agent that understands what you want to configure in Oracle ERP and automatically finds and answers the relevant questions.

## 🚀 Quick Start

1. **Setup Qdrant** with your questions (must include `tags` field)
2. **Configure** `.env` with Qdrant connection
3. **Run** `python app.py`
4. **Open** http://localhost:7860

## 📋 How It Works

1. You describe what you want: *"I need to set up payroll and HR"*
2. AI extracts Oracle module tags: `["payroll", "hr"]`
3. Fetches relevant questions from Qdrant
4. Pre-fills answers using company data
5. Displays results with filters

## 🏗️ Architecture

```
User Input (Company + Industry + Country + Prompt)
    ↓
Generate/Load Consolidated Company Data (9 phases)
    ↓
Analyze Intent → Extract Tags
    ↓
Fetch Questions from Qdrant (by tags)
    ↓
Pre-fill Answers (using company data)
    ↓
Display & Export
```

## 🔑 Key Files

- `app.py` - Main application
- `qdrant_retriever.py` - Question retrieval
- `intent_analyzer.py` - Intent extraction
- `answer_filler.py` - Answer pre-filling
- `phase_extractors/` - Company data generation

## 📦 Requirements

```bash
pip install gradio qdrant-client pandas python-dotenv tavily-python openai
```

## ⚙️ Configuration

Create `.env`:
```bash
# LLM API
ARGUS_MODEL_ID=your-model
ARGUS_API_KEY=your-key
ARGUS_BASE_URL=your-url

# Tavily (for company research)
TAVILY_API_KEY=your-key

# Qdrant (for questions)
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=oracle_questions
```

## 🏷️ Question Format

Your questions in Qdrant must have:

```json
{
  "id": "Q001",
  "categoryID": "Payroll_Configuration",
  "questions": "What is the pay frequency?",
  "mandatoryField": "Pay Frequency",
  "isrequired": true,
  "tags": ["payroll", "hr"]  // Critical for intent matching!
}
```

## 🎯 Supported Tags

Configure in `intent_analyzer.py`:

- `payroll`, `hr`, `hcm` - Human resources
- `gl`, `payables`, `receivables` - Finance
- `fa` - Fixed assets
- `procurement`, `inventory` - Supply chain
- `projects`, `expenses` - Project management
- `revenue`, `budgeting`, `tax` - Other modules

## 📊 Output

- Filtered questions based on intent
- Pre-filled answers from company data
- Exportable JSON: `output/{company}/filled_questionnaire.json`

## 🧪 Testing

```bash
# Test Qdrant connection
python test_qdrant.py

# Run preflight check
python preflight_check.py
```

## 📝 Example

**Input:**
```
Company: Apple Inc.
Industry: Technology
Country: United States
Prompt: I need payroll and HR setup
```

**Result:**
- Generates Apple's company profile (9 phases)
- Identifies tags: `["payroll", "hr", "hcm"]`
- Fetches 50-60 relevant questions
- Pre-fills all answers
- Exports to JSON

## 🔄 Smart Caching

- **First run**: ~3-5 min (generates all company data)
- **Subsequent runs**: ~30 sec (loads cached data)

## 📚 Documentation

- `START_HERE.md` - Quick start guide
- `SETUP_GUIDE.md` - Detailed setup
- `ARCHITECTURE.md` - System design

## 🤝 Contributing

This is a specialized Oracle ERP configuration tool. Customize:
- Tags in `intent_analyzer.py`
- Phase extractors in `phase_extractors/`
- System prompts for better answers

## 📄 License

MIT
