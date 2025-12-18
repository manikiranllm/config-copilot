#!/usr/bin/env python
"""
Config-Copilot - Intent-Driven Oracle ERP Configuration Agent
"""

# Fix for Python 3.13 audioop issue
import sys
from unittest.mock import MagicMock
sys.modules['audioop'] = MagicMock()

# CRITICAL: Load environment variables FIRST before any other imports
import os
from dotenv import load_dotenv
load_dotenv(override=True)

import json
import logging
import asyncio
import gradio as gr
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('config_copilot.log')
    ]
)
logger = logging.getLogger(__name__)

# Import phase extractors
from phase_extractors import get_phase_extractor, get_available_phases

# Import LLM wrapper
from llm_wrapper import call_llm_api_async

# Import new modules
from qdrant_retriever import QuestionRetriever
from intent_analyzer import extract_intent_tags, validate_and_expand_tags
from answer_filler import prefill_answers_from_consolidated, export_filled_questions

# Output directory
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "output"))
OUTPUT_DIR.mkdir(exist_ok=True)

# Phase names
PHASE_NAMES = {
    1: "Company Discovery & Basic Information",
    2: "Industry-Specific Research",
    3: "Enterprise Structure Design",
    4: "Chart of Accounts Framework",
    5: "Currency & Localization",
    6: "Process & Workflow Design",
    7: "Risk & Compliance Framework",
    8: "Integration & Technology Context",
    9: "Implementation Planning"
}

PHASE_TO_SECTION_MAPPING = {
    1: "companyProfile",
    2: "industryAnalysis",
    3: "enterpriseStructure",
    4: "chartOfAccounts",
    5: "currencyLocalization",
    6: "processWorkflow",
    7: "riskCompliance",
    8: "integrationTechnology",
    9: "implementationPlanning"
}

# Global storage
QUESTIONNAIRE_DATA = {}
CURRENT_FILLED_QUESTIONS = []

# Initialize Question API retriever
try:
    question_retriever = QuestionRetriever()
    logger.info("✅ Question API retriever initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize Question API: {e}")
    question_retriever = None


async def process_single_phase(company_name: str, industry: str, country: str, phase_num: int) -> Dict:
    """Process a single phase and generate JSON"""
    try:
        logger.info(f"🚀 Starting Phase {phase_num}: {PHASE_NAMES[phase_num]}")
        
        if phase_num not in get_available_phases():
            error_msg = f"Phase {phase_num} extractor not implemented"
            logger.error(f"❌ {error_msg}")
            return {"phase": phase_num, "status": "failed", "error": error_msg}
        
        extractor = get_phase_extractor(phase_num)
        extracted_json = await extractor.extract_json_fields(
            company_name=company_name,
            industry=industry,
            country=country,
            call_llm_api_async=call_llm_api_async,
            is_cancelled_callback=lambda: False
        )
        
        logger.info(f"✅ Phase {phase_num} completed - {len(extracted_json)} fields")
        
        company_output_dir = OUTPUT_DIR / company_name.replace(" ", "_").lower()
        company_output_dir.mkdir(exist_ok=True)
        
        phase_file = company_output_dir / f"phase{phase_num}.json"
        with open(phase_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_json, f, indent=2, ensure_ascii=False)
        
        return {"phase": phase_num, "status": "completed", "fields_count": len(extracted_json)}
        
    except Exception as e:
        logger.error(f"❌ Phase {phase_num} error: {str(e)}")
        return {"phase": phase_num, "status": "failed", "error": str(e)}


async def generate_consolidated_json(company_name: str) -> Dict:
    """Generate consolidated JSON from all phases"""
    try:
        company_output_dir = OUTPUT_DIR / company_name.replace(" ", "_").lower()
        consolidated_data = {}
        
        for phase_num in range(1, 10):
            phase_file = company_output_dir / f"phase{phase_num}.json"
            if phase_file.exists():
                with open(phase_file, 'r') as f:
                    phase_data = json.load(f)
                clean_data = {k: v for k, v in phase_data.items() if not k.startswith('_')}
                consolidated_data[PHASE_TO_SECTION_MAPPING.get(phase_num)] = clean_data
        
        consolidated_file = company_output_dir / "consolidated.json"
        with open(consolidated_file, 'w') as f:
            json.dump(consolidated_data, f, indent=2)
        
        logger.info(f"✅ Consolidated data saved: {len(consolidated_data)} sections")
        return {"status": "success", "data": consolidated_data}
    except Exception as e:
        logger.error(f"❌ Consolidation error: {e}")
        return {"status": "error", "error": str(e)}


async def process_with_intent(
    company_name: str, 
    industry: str, 
    country: str, 
    user_prompt: str,
    progress=gr.Progress()
) -> Tuple[str, str, pd.DataFrame]:
    """
    Main processing pipeline with intent-driven question filtering
    
    Returns:
        (status_markdown, intent_analysis_markdown, questions_dataframe)
    """
    
    global QUESTIONNAIRE_DATA, CURRENT_FILLED_QUESTIONS
    
    if not all([company_name, industry, country, user_prompt]):
        return "❌ Error: All fields are required!", "", pd.DataFrame()
    
    try:
        # Step 1: Check for existing consolidated data or generate it
        progress(0.1, desc="Step 1/5: Checking consolidated data...")
        logger.info(f"🏢 Processing: {company_name}")
        
        company_output_dir = OUTPUT_DIR / company_name.replace(" ", "_").lower()
        consolidated_file = company_output_dir / "consolidated.json"
        
        if consolidated_file.exists():
            logger.info(f"📂 Found existing consolidated data for {company_name}")
            with open(consolidated_file, 'r') as f:
                consolidated_data = json.load(f)
        else:
            logger.info(f"🔄 Generating consolidated data for {company_name}...")
            progress(0.2, desc="Generating company data (9 phases)...")
            
            # Process all phases
            results = []
            batch_size = 3
            all_phases = list(range(1, 10))
            
            for batch_start in range(0, len(all_phases), batch_size):
                batch_phases = all_phases[batch_start:batch_start + batch_size]
                batch_num = (batch_start // batch_size) + 1
                
                progress(0.2 + (batch_start / 9 * 0.3), desc=f"Processing batch {batch_num}/3...")
                
                tasks = [process_single_phase(company_name, industry, country, p) for p in batch_phases]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if not isinstance(result, Exception):
                        results.append(result)
                
                if batch_start + batch_size < len(all_phases):
                    await asyncio.sleep(2)
            
            progress(0.5, desc="Consolidating data...")
            consolidated_result = await generate_consolidated_json(company_name)
            
            if consolidated_result["status"] != "success":
                return f"❌ Failed to generate consolidated data: {consolidated_result.get('error')}", "", pd.DataFrame()
            
            consolidated_data = consolidated_result["data"]
        
        # Step 2: Analyze user intent
        progress(0.6, desc="Step 2/5: Analyzing your intent...")
        logger.info(f"🤔 Analyzing intent from prompt: {user_prompt[:100]}...")
        
        intent_result = await extract_intent_tags(user_prompt, company_name, industry, country)
        extracted_tags = intent_result.get("tags", [])
        reasoning = intent_result.get("reasoning", "")
        focus_areas = intent_result.get("focus_areas", [])
        
        intent_md = f"""## 🎯 Intent Analysis

**Identified Oracle Modules**: {', '.join(extracted_tags)}

**Reasoning**: {reasoning}

**Focus Areas**: {', '.join(focus_areas)}
"""
        
        # Step 3: Fetch questions from Question API
        progress(0.7, desc="Step 3/5: Fetching relevant questions...")
        
        if not question_retriever:
            return "❌ Question API retriever not available", intent_md, pd.DataFrame()
        
        # Validate tags against available tags
        available_tags = question_retriever.get_all_available_tags()
        valid_tags = await validate_and_expand_tags(extracted_tags, available_tags)
        
        if not valid_tags:
            return f"❌ No valid tags found. Available tags: {available_tags[:10]}", intent_md, pd.DataFrame()
        
        logger.info(f"✅ Using tags: {valid_tags}")
        questions = question_retriever.fetch_questions_by_tags(valid_tags)
        
        if not questions:
            return f"❌ No questions found for tags: {valid_tags}", intent_md, pd.DataFrame()
        
        logger.info(f"📋 Retrieved {len(questions)} questions")
        
        # Step 4: Pre-fill answers using consolidated data
        progress(0.8, desc="Step 4/5: Pre-filling answers...")
        
        filled_questions = await prefill_answers_from_consolidated(
            questions=questions,
            consolidated_data=consolidated_data,
            company=company_name,
            industry=industry,
            country=country
        )
        
        # Step 5: Export and display
        progress(0.9, desc="Step 5/5: Preparing results...")
        
        export_path = export_filled_questions(filled_questions, company_name, OUTPUT_DIR)
        logger.info(f"💾 Exported to: {export_path}")
        
        # Store globally for category filtering
        CURRENT_FILLED_QUESTIONS = filled_questions
        QUESTIONNAIRE_DATA = {}
        for q in filled_questions:
            category = q.get("categoryID", "General")
            if category not in QUESTIONNAIRE_DATA:
                QUESTIONNAIRE_DATA[category] = []
            QUESTIONNAIRE_DATA[category].append(q)
        
        # Create DataFrame for display - ONLY Question and Answer
        df = pd.DataFrame([
            {
                "Question": q["questions"],
                "Answer": q.get("answer", "")
            }
            for q in filled_questions
        ])
        
        progress(1.0, desc="Complete!")
        
        status_md = f"""## ✅ Configuration Ready

**Company**: {company_name}  
**Questions Retrieved**: {len(filled_questions)}  
**Categories**: {len(QUESTIONNAIRE_DATA)}  
**Export Location**: `{export_path}`

You can now review and edit the answers below. Select a category to filter questions.
"""
        
        return status_md, intent_md, df
        
    except Exception as e:
        logger.error(f"❌ Processing error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return f"❌ Error: {str(e)}", "", pd.DataFrame()


def filter_by_category(category_name: str, current_df: pd.DataFrame) -> pd.DataFrame:
    """Filter questions by selected category"""
    
    if not category_name or category_name == "All":
        return current_df
    
    if category_name not in QUESTIONNAIRE_DATA:
        return pd.DataFrame(columns=["Question", "Answer"])
    
    category_questions = QUESTIONNAIRE_DATA[category_name]
    
    # Create filtered dataframe with only questions from this category
    filtered_df = pd.DataFrame([
        {
            "Question": q["questions"],
            "Answer": q.get("answer", "")
        }
        for q in category_questions
    ])
    
    return filtered_df


def create_gradio_interface():
    """Create Gradio interface"""
    
    with gr.Blocks(title="Config-Copilot Agent", theme=gr.themes.Soft()) as app:
        gr.Markdown("""
        # 🤖 Config-Copilot - Oracle ERP Configuration Agent
        
        **Intent-Driven Configuration**: Tell us what you want to configure, and we'll fetch and answer relevant questions.
        
        ### How it works:
        1. **Generate/Load Data**: We create consolidated company data (or load existing)
        2. **Understand Intent**: AI analyzes your prompt to identify relevant Oracle modules
        3. **Fetch Questions**: Retrieve questions from Question API based on identified tags
        4. **Pre-fill Answers**: Automatically answer questions using company data
        5. **Review & Edit**: You can review and modify answers before export
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                company_input = gr.Textbox(
                    label="Company Name",
                    placeholder="e.g., Apple Inc.",
                    info="Enter the company name"
                )
            with gr.Column(scale=1):
                industry_input = gr.Textbox(
                    label="Industry",
                    placeholder="e.g., Technology",
                    info="Company's industry sector"
                )
            with gr.Column(scale=1):
                country_input = gr.Textbox(
                    label="Country",
                    placeholder="e.g., United States",
                    info="Primary country of operation"
                )
        
        prompt_input = gr.Textbox(
            label="What do you want to configure?",
            placeholder="e.g., I need to set up payroll and HR management for our new employees",
            lines=3,
            info="Describe what you want to configure in Oracle ERP"
        )
        
        generate_btn = gr.Button("🚀 Generate Configuration", variant="primary", size="lg")
        
        gr.Markdown("---")
        
        status_output = gr.Markdown()
        intent_output = gr.Markdown()
        
        gr.Markdown("## 📊 Questions & Answers")
        
        with gr.Row():
            category_filter = gr.Dropdown(
                label="Filter by Category",
                choices=["All"],
                value="All",
                interactive=True
            )
        
        questions_df = gr.Dataframe(
            label="Questions",
            interactive=False,
            wrap=True
        )
        
        gr.Markdown("""
        ### 💡 Tips:
        - If data already exists for a company, it will be loaded instantly
        - Be specific in your prompt to get the most relevant questions
        - All answers are pre-filled but can be edited in the exported JSON file
        - Check the export location in the status message above
        """)
        
        # Store the full dataframe
        full_df_state = gr.State(pd.DataFrame())
        
        # Generate button click
        def on_generate(company, industry, country, prompt):
            status, intent, df = asyncio.run(
                process_with_intent(company, industry, country, prompt)
            )
            
            # Update category choices from global QUESTIONNAIRE_DATA
            if QUESTIONNAIRE_DATA:
                categories = ["All"] + sorted(QUESTIONNAIRE_DATA.keys())
            else:
                categories = ["All"]
            
            return (
                status,
                intent,
                df,
                df,  # full_df_state
                gr.Dropdown(choices=categories, value="All")
            )
        
        generate_btn.click(
            fn=on_generate,
            inputs=[company_input, industry_input, country_input, prompt_input],
            outputs=[status_output, intent_output, questions_df, full_df_state, category_filter]
        )
        
        # Category filter change
        def on_category_filter(category, full_df):
            if full_df.empty:
                return full_df
            return filter_by_category(category, full_df)
        
        category_filter.change(
            fn=on_category_filter,
            inputs=[category_filter, full_df_state],
            outputs=[questions_df]
        )
    
    return app


if __name__ == "__main__":
    logger.info("🚀 Starting Config-Copilot Agent with Intent Analysis")
    
    # Check Question API configuration
    api_url = os.getenv("QUESTION_API_URL", "https://runpodroute.preprod.opkeyone.com/GenericRAGDev/api/v1/query/search")
    collection = os.getenv("QUESTION_COLLECTION", "questionnaire_items")
    logger.info(f"📊 Question API: {api_url}")
    logger.info(f"📊 Collection: {collection}")
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    app = create_gradio_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
