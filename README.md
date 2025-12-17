# Config-Copilot 🚀

AI-powered Oracle Fusion ERP configuration automation system that intelligently fills 187 questionnaire questions through multi-phase research and analysis.

## Features

- **9-Phase Research Pipeline**: Automated discovery across company profile, industry analysis, enterprise structure, chart of accounts, and more
- **Smart Caching**: Reuses existing analysis to skip redundant processing
- **Intelligent Questionnaire Filling**: Uses Claude API (Argus) to generate contextual answers
- **Interactive UI**: Gradio-based interface with category-organized question display
- **Batch Processing**: Efficient 3-phase parallel processing for faster results

## Architecture

```
config_copilot/
├── app.py                          # Main Gradio application
├── phase_extractors/               # Modular phase processors
├── questionnaire_filler_argus.py   # Claude API integration for Q&A
├── llm_wrapper.py                  # LLM API wrapper
├── argus_wrapper.py                # Argus-specific wrapper
└── oracle_system_questionnnaire.json  # Question template
```

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/config-copilot.git
cd config-copilot
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

Required variables:
- `ARGUS_MODEL_ID`: Your Claude model identifier
- `ARGUS_API_KEY`: Your Anthropic API key
- `TAVILY_API_KEY`: For web research
- `OUTPUT_DIR`: Output directory path (default: `output`)

## Usage

1. **Start the application**
```bash
python app.py
```

2. **Access the web interface**
- Open browser to `http://localhost:7860`

3. **Generate configuration**
- Enter company name, industry, and country
- Click "Generate Configuration"
- Wait for 9-phase processing (or instant load if cached)
- Review and edit 187 questions organized by category

## How It Works

1. **Phase Processing**: 9 distinct research phases gather comprehensive company data
2. **Consolidation**: Phase results merge into unified JSON structure
3. **Intelligent Filling**: Claude API analyzes consolidated data and generates contextual answers
4. **Interactive Review**: Category-organized UI for answer validation and editing

## Tech Stack

- **Frontend**: Gradio
- **Backend**: FastAPI, Python 3.9+
- **AI**: Claude API (Anthropic), Tavily Search API
- **Data**: JSON-based storage with smart caching

## Project Structure

- **Phase Extractors**: Modular research phases (1-9)
- **LLM Integration**: Async Claude API calls with retry logic
- **State Management**: Global questionnaire data store
- **Output Management**: Company-specific directories with versioning

## Development

```bash
# Install in development mode
pip install -e .

# Run with debug logging
LOG_LEVEL=DEBUG python app.py
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or submit a PR.

## Author

Mani Kiran Gadi - Opkey
