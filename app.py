#!/usr/bin/env python
"""
Config-Copilot - Gradio Interface with Category Dropdown Questionnaire
"""

# Fix for Python 3.13 audioop issue
import sys
from unittest.mock import MagicMock
sys.modules['audioop'] = MagicMock()

# CRITICAL: Load environment variables FIRST before any other imports
import os
from dotenv import load_dotenv
load_dotenv(override=True)  # Force reload to ensure we get latest values

# Verify Argus configuration is loaded
ARGUS_MODEL = os.getenv("ARGUS_MODEL_ID")
if ARGUS_MODEL:
    print(f"✅ Argus Model loaded in app.py: {ARGUS_MODEL}")
else:
    print("❌ WARNING: Argus configuration not found in app.py!")

import json
import logging
import asyncio
import gradio as gr
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Tuple

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

# Import questionnaire filler (using Argus API version)
from questionnaire_filler_argus import fill_questionnaire_with_consolidated_data, export_questionnaire_to_json

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

# Global storage for questionnaire
QUESTIONNAIRE_DATA = {}


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


async def generate_all_phases(company_name: str, industry: str, country: str, progress=gr.Progress()):
    """Process all 9 phases in batches of 3"""
    
    global QUESTIONNAIRE_DATA
    
    if not company_name or not industry or not country:
        return "❌ Error: All fields required!", [], [], False
    
    logger.info(f"🏢 Starting analysis for {company_name}")
    
    # Check if consolidated data already exists
    company_output_dir = OUTPUT_DIR / company_name.replace(" ", "_").lower()
    consolidated_file = company_output_dir / "consolidated.json"
    
    if consolidated_file.exists():
        logger.info(f"📂 Found existing consolidated data for {company_name}, skipping phase processing")
        progress(0.5, desc="Loading existing data...")
        
        try:
            with open(consolidated_file, 'r') as f:
                consolidated_data = json.load(f)
            
            logger.info(f"✅ Loaded existing consolidated data with {len(consolidated_data)} sections")
            
            # Jump directly to questionnaire filling
            progress(0.9, desc="Filling questionnaire from existing data...")
            
            filled_questions = []
            category_choices = []
            
            try:
                logger.info(f"🔄 Calling Claude API to fill questionnaire...")
                filled_questions = await fill_questionnaire_with_consolidated_data(
                    consolidated_data, company_name, industry, country
                )
                
                export_questionnaire_to_json(filled_questions, company_name, OUTPUT_DIR)
                
                # Store globally
                QUESTIONNAIRE_DATA = {}
                for q in filled_questions:
                    category = q.get("categoryID", "General")
                    if category not in QUESTIONNAIRE_DATA:
                        QUESTIONNAIRE_DATA[category] = []
                    QUESTIONNAIRE_DATA[category].append(q)
                
                category_choices = sorted(QUESTIONNAIRE_DATA.keys())
                
                logger.info(f"✅ Questionnaire: {len(filled_questions)} questions in {len(category_choices)} categories")
                
            except Exception as e:
                logger.error(f"❌ Questionnaire failed: {e}")
                import traceback
                logger.error(traceback.format_exc())
            
            progress(1.0, desc="Complete!")
            
            summary = f"""
## ✅ Configuration Ready for {company_name}

**Select a category below to review and edit {len(filled_questions)} questions across {len(category_choices)} categories**
"""
            
            return summary, filled_questions, category_choices, True
            
        except Exception as e:
            logger.error(f"❌ Error loading existing data: {e}")
            logger.info(f"⚠️ Will proceed with full processing")
            # Continue with normal processing if loading fails
    
    # Normal processing continues here...
    results = []
    progress(0, desc="Starting analysis...")
    
    batch_size = 3
    all_phases = list(range(1, 10))
    
    for batch_start in range(0, len(all_phases), batch_size):
        batch_phases = all_phases[batch_start:batch_start + batch_size]
        batch_num = (batch_start // batch_size) + 1
        
        progress(batch_start / 9, desc=f"Batch {batch_num}/3: Phases {batch_phases}...")
        
        tasks = [process_single_phase(company_name, industry, country, phase_num) for phase_num in batch_phases]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in batch_results:
            if not isinstance(result, Exception):
                results.append(result)
        
        if batch_start + batch_size < len(all_phases):
            await asyncio.sleep(2)
    
    progress(0.95, desc="Consolidating...")
    consolidated_result = await generate_consolidated_json(company_name)
    
    progress(0.97, desc="Filling questionnaire...")
    
    filled_questions = []
    category_choices = []
    
    if consolidated_result["status"] == "success":
        try:
            filled_questions = await fill_questionnaire_with_consolidated_data(
                consolidated_result["data"], company_name, industry, country
            )
            
            export_questionnaire_to_json(filled_questions, company_name, OUTPUT_DIR)
            
            # Store globally
            QUESTIONNAIRE_DATA = {}
            for q in filled_questions:
                category = q.get("categoryID", "General")
                if category not in QUESTIONNAIRE_DATA:
                    QUESTIONNAIRE_DATA[category] = []
                QUESTIONNAIRE_DATA[category].append(q)
            
            category_choices = sorted(QUESTIONNAIRE_DATA.keys())
            
            logger.info(f"✅ Questionnaire: {len(filled_questions)} questions in {len(category_choices)} categories")
            
        except Exception as e:
            logger.error(f"❌ Questionnaire failed: {e}")
    
    progress(1.0, desc="Complete!")
    
    completed = len([r for r in results if r["status"] == "completed"])
    
    summary = f"""
## ✅ Configuration Ready for {company_name}

**Select a category below to review and edit {len(filled_questions)} questions across {len(category_choices)} categories**
"""
    
    return (
        summary,
        filled_questions,
        category_choices,  # Just return the list
        True  # visibility for questions_container
    )


async def generate_consolidated_json(company_name: str) -> Dict:
    """Generate consolidated JSON"""
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
        
        return {"status": "success", "data": consolidated_data}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def display_category_questions(category_name: str) -> List:
    """Display questions for selected category"""
    
    if not category_name or category_name not in QUESTIONNAIRE_DATA:
        return []
    
    questions = QUESTIONNAIRE_DATA[category_name]
    
    components = [
        gr.Markdown(f"## 📂 {category_name.replace('_', ' ')}"),
        gr.Markdown(f"*{len(questions)} questions in this category*"),
        gr.Markdown("---")
    ]
    
    for q in questions:
        q_id = q["id"]
        question_text = q.get("questions", "")
        mandatory_field = q.get("mandatoryField", "")
        answer = q.get("answer", "")
        is_required = q.get("isrequired", False)
        
        req_icon = "✅" if is_required else "⚪"
        label = f"{req_icon} Q{q_id}: {mandatory_field}"
        
        components.append(
            gr.Textbox(
                label=label,
                value=answer if answer else "",
                placeholder="",
                lines=1,
                interactive=True,
                info=question_text if question_text else None
            )
        )
    
    return components


def format_category_questions_as_markdown(category_name: str) -> str:
    """Format category questions as markdown for display"""
    
    if not category_name or category_name not in QUESTIONNAIRE_DATA:
        return "**No questions found**"
    
    questions = QUESTIONNAIRE_DATA[category_name]
    
    markdown = f"## 📂 {category_name.replace('_', ' ')}\n\n"
    markdown += f"*{len(questions)} questions in this category*\n\n"
    markdown += "---\n\n"
    
    for q in questions:
        q_id = q["id"]
        question_text = q.get("questions", "")
        mandatory_field = q.get("mandatoryField", "")
        answer = q.get("answer", "")
        is_required = q.get("isrequired", False)
        
        req_icon = "✅" if is_required else "⚪"
        
        markdown += f"### {req_icon} Q{q_id}: {mandatory_field}\n\n"
        
        if question_text:
            markdown += f"**Question**: {question_text}\n\n"
        
        if answer:
            markdown += f"**Answer**: `{answer}`\n\n"
        else:
            markdown += f"**Answer**: *Not filled*\n\n"
        
        markdown += "---\n\n"
    
    return markdown


def generate_textbox_updates_for_category(category_name: str) -> List:
    """Generate gr.update() objects for textboxes based on selected category"""
    
    if not category_name or category_name not in QUESTIONNAIRE_DATA:
        # Hide all textboxes if no category
        return [gr.update(visible=False) for _ in range(50)]
    
    questions = QUESTIONNAIRE_DATA[category_name]
    updates = []
    
    for i in range(50):
        if i < len(questions):
            q = questions[i]
            q_id = q["id"]
            question_text = q.get("questions", "")
            mandatory_field = q.get("mandatoryField", "")
            answer = q.get("answer", "")
            is_required = q.get("isrequired", False)
            
            req_icon = "✅" if is_required else "⚪"
            label = f"{req_icon} Q{q_id}: {mandatory_field}"
            
            # Create update with visible textbox
            updates.append(gr.update(
                label=label,
                value=answer if answer else "",
                visible=True,
                interactive=True,
                info=question_text if question_text else None,
                placeholder="Enter answer here..."
            ))
        else:
            # Hide unused textboxes
            updates.append(gr.update(visible=False))
    
    return updates


def create_gradio_interface():
    """Create Gradio interface"""
    
    with gr.Blocks(title="Config-Copilot", theme=gr.themes.Soft()) as app:
        gr.Markdown("""
        # 🚀 OpKey ERP Configuration - Oracle Fusion Setup
        
        Generate Oracle Fusion ERP configuration with auto-filled questionnaire (187 questions)
        
        **Tip**: If you've already processed a company, just enter the same name to reload existing data!
        """)
        
        with gr.Row():
            company_input = gr.Textbox(label="Company Name", placeholder="e.g., Apple Inc.")
            industry_input = gr.Textbox(label="Industry", placeholder="e.g., Technology")
            country_input = gr.Textbox(label="Country", placeholder="e.g., United States")
        
        generate_btn = gr.Button("🚀 Generate Configuration", variant="primary", size="lg")
        
        gr.Markdown("---")
        
        summary_output = gr.Markdown()
        
        gr.Markdown("## 📋 Oracle System Questionnaire")
        
        # Questionnaire state
        questions_state = gr.State([])
        
        # Category selector
        with gr.Row():
            category_dropdown = gr.Dropdown(
                label="Select Category",
                choices=[],
                visible=False,
                interactive=True
            )
        
        # Container for dynamic question textboxes (max 50 questions per category should be enough)
        with gr.Column(visible=False) as questions_container:
            gr.Markdown("### Questions will appear here after selecting a category")
            # Pre-create a pool of textboxes (we'll show/hide as needed)
            question_textboxes = []
            for i in range(50):  # Maximum 50 questions per category
                textbox = gr.Textbox(
                    label=f"Question {i+1}",
                    visible=False,
                    interactive=True,
                    lines=1
                )
                question_textboxes.append(textbox)
        
        # Generate button click
        def on_generate_click(c, i, co):
            summary, questions, categories, show_container = asyncio.run(generate_all_phases(c, i, co))
            
            # Update dropdown choices and visibility
            if categories:
                dropdown_choices = categories
                dropdown_value = categories[0]
                dropdown_visible = True
                
                # Generate updates for first category
                first_category_updates = generate_textbox_updates_for_category(categories[0])
            else:
                dropdown_choices = []
                dropdown_value = None
                dropdown_visible = False
                first_category_updates = [gr.update(visible=False) for _ in range(50)]
            
            outputs = [
                summary,
                questions,
                gr.Dropdown(choices=dropdown_choices, value=dropdown_value, visible=dropdown_visible, interactive=True, label="Select Category"),
                gr.update(visible=show_container)
            ]
            outputs.extend(first_category_updates)
            
            return outputs
        
        generate_btn.click(
            fn=on_generate_click,
            inputs=[company_input, industry_input, country_input],
            outputs=[summary_output, questions_state, category_dropdown, questions_container] + question_textboxes
        )
        
        # Category selection change
        def on_category_change(category):
            if not category:
                return [gr.update(visible=False) for _ in range(50)]
            
            return generate_textbox_updates_for_category(category)
        
        category_dropdown.change(
            fn=on_category_change,
            inputs=[category_dropdown],
            outputs=question_textboxes
        )
        

    
    return app


if __name__ == "__main__":
    logger.info("🚀 Starting Config-Copilot with Argus API")
    argus_model = os.getenv("ARGUS_MODEL_ID", "Argus")
    logger.info(f"✅ Using Argus Model: {argus_model}")
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    app = create_gradio_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
