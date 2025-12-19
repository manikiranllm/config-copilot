#!/usr/bin/env python
"""
Config-Copilot - Interactive Conversational Configuration Agent
"""

# Fix for Python 3.13 audioop issue
import sys
from unittest.mock import MagicMock
sys.modules['audioop'] = MagicMock()

import os
from dotenv import load_dotenv
load_dotenv(override=True)

import json
import logging
import asyncio
import gradio as gr
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional

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

# Import modules
from phase_extractors import get_phase_extractor, get_available_phases
from llm_wrapper import call_llm_api_async
from qdrant_retriever import QuestionRetriever
from intent_analyzer import extract_intent_tags, validate_and_expand_tags
from answer_filler import prefill_answers_from_consolidated
from conversational_agent import ConversationalAgent

# Output directory
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "output"))
OUTPUT_DIR.mkdir(exist_ok=True)

# Phase mapping
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

# Global agent instance
agent = None


async def process_single_phase(company_name: str, industry: str, country: str, phase_num: int) -> Dict:
    """Process a single phase and generate JSON"""
    try:
        logger.info(f"🚀 Starting Phase {phase_num}")
        
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


async def initialize_agent(company: str, industry: str, country: str, initial_prompt: str):
    """Initialize the conversational agent with company data"""
    global agent
    
    logger.info(f"🤖 Initializing agent for {company}")
    
    # Create agent instance
    agent = ConversationalAgent(
        company=company,
        industry=industry,
        country=country,
        output_dir=OUTPUT_DIR
    )
    
    # Start initialization in background
    await agent.initialize(initial_prompt)
    
    return agent


def create_questions_html(agent: ConversationalAgent, selected_category: str = None) -> str:
    """Create HTML for questions panel with tabs"""
    
    if not agent:
        return """
        <div style='padding: 30px; text-align: center; background: #f8f9fa; border-radius: 10px;'>
            <div style='font-size: 48px; margin-bottom: 20px;'>👋</div>
            <h3 style='color: #666;'>Welcome to Config-Copilot</h3>
            <p style='color: #999;'>Fill in the details above and click "Start Configuration" to begin.</p>
        </div>
        """
    
    if agent.state["phase"] == "prerequisites":
        # Show prerequisite progress
        prereq_state = agent.prerequisite_manager.state
        total = len(prereq_state["questions"])
        answered = len(prereq_state["answers"])
        progress_pct = (answered / total * 100) if total > 0 else 0
        
        return f"""
        <div style='padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; border-radius: 10px;'>
            <div style='font-size: 48px; margin-bottom: 20px; text-align: center;'>📋</div>
            <h3 style='text-align: center; margin-bottom: 20px;'>Discovery Phase</h3>
            
            <div style='background: rgba(255,255,255,0.2); border-radius: 10px; padding: 15px; margin-bottom: 20px;'>
                <div style='display: flex; justify-content: space-between; margin-bottom: 10px;'>
                    <span>Progress</span>
                    <span><strong>{answered}/{total}</strong> questions</span>
                </div>
                <div style='width: 100%; background: rgba(0,0,0,0.2); border-radius: 10px; height: 10px;'>
                    <div style='width: {progress_pct}%; background: white; border-radius: 10px; height: 100%;'></div>
                </div>
            </div>
            
            <div style='background: rgba(255,255,255,0.15); border-radius: 8px; padding: 15px;'>
                <p style='margin: 0; font-size: 14px; opacity: 0.9;'>
                    💬 Answering prerequisite questions to understand your requirements.
                    Your answers will help pre-configure the system optimally.
                </p>
            </div>
        </div>
        """
    
    if agent.state["phase"] == "generating":
        return """
        <div style='padding: 30px; text-align: center; background: #f8f9fa; border-radius: 10px;'>
            <div style='font-size: 48px; margin-bottom: 20px;'>⏳</div>
            <h3 style='color: #666;'>Generating Company Data...</h3>
            <p style='color: #999;'>Running 9-phase analysis. This may take 2-3 minutes.</p>
        </div>
        """
    
    if agent.state["phase"] == "error":
        return """
        <div style='padding: 30px; text-align: center; background: #fee; border-radius: 10px;'>
            <div style='font-size: 48px; margin-bottom: 20px;'>❌</div>
            <h3 style='color: #c00;'>Error</h3>
            <p>Failed to generate company data. Please try again.</p>
        </div>
        """
    
    if not agent.state["displayed_questions"]:
        return """
        <div style='padding: 30px; text-align: center; background: #f8f9fa; border-radius: 10px;'>
            <div style='font-size: 48px; margin-bottom: 20px;'>💬</div>
            <h3 style='color: #666;'>Ready to Configure</h3>
            <p style='color: #999;'>Start chatting to configure your Oracle ERP system</p>
        </div>
        """
    
    # Build HTML with tabs and questions
    categories = agent.state["categories"]
    
    # If no category selected, show the first one
    if not selected_category and categories:
        selected_category = list(categories.keys())[0]
    
    html = "<div style='font-family: system-ui, -apple-system, sans-serif;'>"
    
    # Summary stats
    html += f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h2 style='margin: 0 0 10px 0;'>📋 Configuration Overview</h2>
        <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px;'>
            <div style='background: rgba(255,255,255,0.2); padding: 10px; border-radius: 5px; text-align: center;'>
                <div style='font-size: 24px; font-weight: bold;'>{len(agent.state["displayed_questions"])}</div>
                <div style='font-size: 12px; opacity: 0.9;'>Questions</div>
            </div>
            <div style='background: rgba(255,255,255,0.2); padding: 10px; border-radius: 5px; text-align: center;'>
                <div style='font-size: 24px; font-weight: bold;'>{len(categories)}</div>
                <div style='font-size: 12px; opacity: 0.9;'>Categories</div>
            </div>
            <div style='background: rgba(255,255,255,0.2); padding: 10px; border-radius: 5px; text-align: center;'>
                <div style='font-size: 24px; font-weight: bold;'>{len(agent.state["current_tags"])}</div>
                <div style='font-size: 12px; opacity: 0.9;'>Modules</div>
            </div>
        </div>
    </div>
    """
    
    # Tabs
    if categories:
        html += "<div style='margin-bottom: 20px;'>"
        html += "<div style='border-bottom: 2px solid #e0e0e0; margin-bottom: 20px;'>"
        html += "<div style='display: flex; gap: 5px; flex-wrap: wrap;'>"
        
        for idx, category in enumerate(categories.keys()):
            question_count = len(categories[category])
            active = idx == 0
            bg_color = "#667eea" if active else "#f5f5f5"
            text_color = "white" if active else "#666"
            
            html += f"""
            <div style='padding: 12px 20px; background: {bg_color}; color: {text_color}; 
                        border-radius: 8px 8px 0 0; font-weight: 600; font-size: 14px;
                        border: 2px solid {"#667eea" if active else "#e0e0e0"}; border-bottom: none;'>
                {category} ({question_count})
            </div>
            """
        
        html += "</div></div></div>"
    
    # Questions list - filter by selected category
    html += "<div style='max-height: 600px; overflow-y: auto;'>"    
    
    # Determine which categories to display
    if selected_category and selected_category != "All" and selected_category in categories:
        categories_to_show = {selected_category: categories[selected_category]}
    else:
        categories_to_show = categories
    
    for category, questions in categories_to_show.items():
        html += f"""
        <div style='margin-bottom: 30px; background: white; border-radius: 10px; 
                    padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
            <h3 style='color: #667eea; margin: 0 0 20px 0; font-size: 18px; 
                       border-bottom: 2px solid #667eea; padding-bottom: 10px;'>
                📂 {category}
            </h3>
        """
        
        for q in questions:
            answer = q.get("answer", "")
            has_answer = answer and answer != "Not Available"
            icon = "✅" if has_answer else "⏳"
            answer_color = "#2d8659" if has_answer else "#999"
            
            html += f"""
            <div style='margin-bottom: 20px; padding: 15px; background: #f8f9fa; 
                        border-left: 4px solid {"#2d8659" if has_answer else "#e0e0e0"}; border-radius: 5px;'>
                <div style='font-weight: 600; color: #333; margin-bottom: 8px; font-size: 14px;'>
                    {icon} {q["questions"]}
                </div>
                <div style='color: {answer_color}; font-size: 13px; padding-left: 20px; 
                            font-style: {"normal" if has_answer else "italic"};'>
                    {answer if has_answer else "Waiting for information..."}
                </div>
            </div>
            """
        
        html += "</div>"
    
    html += "</div></div>"
    
    return html


def create_status_html(agent: Optional[ConversationalAgent]) -> str:
    """Create status message HTML"""
    
    if not agent:
        return """
        <div style='padding: 15px; background: #e3f2fd; border-left: 4px solid #2196f3; border-radius: 5px;'>
            <strong>👋 Welcome to Config-Copilot</strong>
            <p style='margin: 10px 0 0 0; color: #666;'>Fill in the details above and click "Start Configuration" to begin.</p>
        </div>
        """
    
    if agent.state["phase"] == "prerequisites":
        prereq_state = agent.prerequisite_manager.state
        answered = len(prereq_state["answers"])
        total = len(prereq_state["questions"])
        
        return f"""
        <div style='padding: 15px; background: #f3e5f5; border-left: 4px solid #9c27b0; border-radius: 5px;'>
            <strong>📋 Discovery Phase</strong>
            <p style='margin: 10px 0 0 0; color: #666;'>
                Answering prerequisite questions ({answered}/{total} completed). 
                Your answers help me understand your requirements better.
            </p>
        </div>
        """
    
    if agent.state["phase"] == "generating":
        return """
        <div style='padding: 15px; background: #fff3e0; border-left: 4px solid #ff9800; border-radius: 5px;'>
            <strong>⏳ Processing...</strong>
            <p style='margin: 10px 0 0 0; color: #666;'>Running 9-phase company analysis. This will take 2-3 minutes.</p>
        </div>
        """
    
    if agent.state["phase"] == "ready":
        return f"""
        <div style='padding: 15px; background: #e8f5e9; border-left: 4px solid #4caf50; border-radius: 5px;'>
            <strong>✅ Ready!</strong>
            <p style='margin: 10px 0 0 0; color: #666;'>
                Found {len(agent.state["displayed_questions"])} questions across {len(agent.state["categories"])} categories. 
                Start chatting to refine your configuration!
            </p>
        </div>
        """
    
    if agent.state["phase"] == "conversing":
        return f"""
        <div style='padding: 15px; background: #f3e5f5; border-left: 4px solid #9c27b0; border-radius: 5px;'>
            <strong>💬 Configuring...</strong>
            <p style='margin: 10px 0 0 0; color: #666;'>
                Active modules: {', '.join(agent.state["current_tags"])}
            </p>
        </div>
        """
    
    return ""


async def handle_start_configuration(company: str, industry: str, country: str, initial_prompt: str):
    """Handle the initial form submission"""
    
    if not all([company, industry, country, initial_prompt]):
        return (
            "<div style='padding: 15px; background: #ffebee; border-left: 4px solid #f44336; border-radius: 5px;'>" 
            "<strong>❌ Error</strong><p style='margin: 10px 0 0 0;'>All fields are required!</p></div>",
            gr.update(choices=["All"], value="All"),
            "",
            [],
            gr.update(interactive=False)
        )
    
    # Initialize agent
    await initialize_agent(company, industry, country, initial_prompt)
    
    # Return initial state
    status_html = create_status_html(agent)
    questions_html = create_questions_html(agent, "All")
    
    # Get categories for dropdown
    categories = ["All"] + list(agent.state["categories"].keys()) if agent and agent.state.get("categories") else ["All"]
    
    # Initial bot message
    initial_message = [
        (None, "⏳ Analyzing your company and generating configuration data. This will take 2-3 minutes...")
    ]
    
    return (
        status_html,
        gr.update(choices=categories, value="All"),
        questions_html,
        initial_message,
        gr.update(interactive=True)
    )


async def handle_chat_message(message: str, history: list):
    """Handle user chat messages"""
    
    global agent
    
    if not agent:
        return history + [(message, "⚠️ Please start configuration first by clicking 'Start Configuration' button.")]
    
    if agent.state["phase"] == "generating":
        return history + [(message, "⏳ Please wait while I finish analyzing your company data...")]
    
    # Process message through agent
    bot_response = await agent.process_message(message)
    
    # Return updated history
    return history + [(message, bot_response)]


async def refresh_questions_panel(selected_category="All"):
    """Refresh the questions panel after chat interaction"""
    global agent
    
    if not agent:
        return "", gr.update(choices=["All"], value="All"), ""
    
    questions_html = create_questions_html(agent, selected_category)
    status_html = create_status_html(agent)
    
    # Update categories dropdown
    categories = ["All"] + list(agent.state["categories"].keys()) if agent.state.get("categories") else ["All"]
    
    return status_html, gr.update(choices=categories, value=selected_category), questions_html


async def handle_category_change(selected_category):
    """Handle category dropdown change"""
    global agent
    
    if not agent:
        return ""
    
    return create_questions_html(agent, selected_category)


def create_gradio_interface():
    """Create the interactive Gradio interface"""
    
    with gr.Blocks(title="Config-Copilot Interactive", theme=gr.themes.Soft()) as app:
        
        gr.Markdown("""
        # 🤖 Config-Copilot - Interactive Oracle ERP Configuration
        
        **AI-Powered Conversational Configuration**: Chat with the AI to configure your Oracle ERP system dynamically.
        """)
        
        # Top section: Input form
        with gr.Row():
            with gr.Column(scale=3):
                with gr.Row():
                    company_input = gr.Textbox(
                        label="Company Name",
                        placeholder="e.g., Apple Inc.",
                        scale=1
                    )
                    industry_input = gr.Textbox(
                        label="Industry",
                        placeholder="e.g., Technology",
                        scale=1
                    )
                    country_input = gr.Textbox(
                        label="Country",
                        placeholder="e.g., United States",
                        scale=1
                    )
            
            with gr.Column(scale=2):
                initial_prompt_input = gr.Textbox(
                    label="What do you want to configure?",
                    placeholder="e.g., Setup payroll and HR for manufacturing company",
                    lines=3
                )
        
        start_btn = gr.Button("🚀 Start Configuration", variant="primary", size="lg")
        
        status_display = gr.HTML()
        
        # Main section: Questions panel + Chat
        with gr.Row():
            # Left panel: Questions
            with gr.Column(scale=2):
                gr.Markdown("## 📋 Configuration Questions")
                
                # Category selector
                category_dropdown = gr.Dropdown(
                    label="Select Category",
                    choices=["All"],
                    value="All",
                    interactive=True
                )
                
                questions_panel = gr.HTML()
            
            # Right panel: Chat
            with gr.Column(scale=1):
                gr.Markdown("## 💬 Configuration Assistant")
                chatbot = gr.Chatbot(
                    height=600,
                    show_label=False
                )
                
                with gr.Row():
                    chat_input = gr.Textbox(
                        placeholder="Ask questions or provide information...",
                        show_label=False,
                        scale=4,
                        interactive=False
                    )
                    send_btn = gr.Button("Send", scale=1, variant="primary")
        
        gr.Markdown("""
        ### 💡 How it works:
        1. **Fill the form above** with your company details and what you want to configure
        2. **Click "Start Configuration"** - The system will analyze your company (takes 2-3 minutes)
        3. **Chat naturally** - Ask questions, provide clarifications, and refine your configuration
        4. **Watch the left panel** - Questions and answers update dynamically as you chat
        5. **Export when ready** - Your configuration is saved automatically
        """)
        
        # Event handlers
        async def on_start(company, industry, country, initial_prompt):
            result = await handle_start_configuration(company, industry, country, initial_prompt)
            # Wait a moment for agent initialization
            await asyncio.sleep(1)
            
            # Get the initial bot message from agent if it exists
            if agent and agent.get_last_assistant_message():
                initial_chat = [(None, agent.get_last_assistant_message())]
                return result[0], result[1], result[2], initial_chat, result[4]
            
            return result
        
        start_btn.click(
            fn=on_start,
            inputs=[company_input, industry_input, country_input, initial_prompt_input],
            outputs=[status_display, category_dropdown, questions_panel, chatbot, chat_input]
        )
        
        # Category dropdown change
        category_dropdown.change(
            fn=handle_category_change,
            inputs=[category_dropdown],
            outputs=[questions_panel]
        )
        
        async def on_chat(message, history):
            # Add user message immediately
            history = history + [(message, None)]
            yield history, "", gr.update(interactive=False)
            
            # Get bot response
            bot_response = await agent.process_message(message) if agent else "Please start configuration first."
            history[-1] = (message, bot_response)
            
            yield history, "", gr.update(interactive=True)
            
            # Refresh questions panel
            status_html, questions_html = await refresh_questions_panel()
            yield history, "", gr.update(interactive=True)
        
        # Chat submission with typing indicator
        async def on_chat_with_typing(message, history):
            """Handle chat with typing indicator"""
            if not message.strip():
                yield history, "", gr.update(interactive=True)
                return
            
            # Add user message + typing indicator
            history = history + [(message, "🤔 Thinking...")]
            yield history, "", gr.update(interactive=False)
            
            # Get bot response (this also runs analysis)
            if agent:
                if agent.state["phase"] == "prerequisites":
                    # In prerequisite phase - get answer directly
                    bot_response = await agent.process_message(message)
                    history[-1] = (message, bot_response)
                    
                elif agent.state["phase"] == "generating":
                    bot_response = "⏳ Please wait while I finish analyzing your company data..."
                    history[-1] = (message, bot_response)
                    
                else:
                    # Normal conversation phase
                    bot_response = await agent.process_message(message)
                    
                    # Get the analysis from conversation history if available
                    if agent.state["conversation_history"]:
                        last_entry = agent.state["conversation_history"][-1]
                        if "analysis" in last_entry:
                            analysis = last_entry["analysis"]
                            reasoning = analysis.get("reasoning", "")
                            
                            if reasoning:
                                # Show analysis first, then response
                                analysis_msg = f"📊 **Analysis:** {reasoning}\n\n---\n\n{bot_response}"
                                history[-1] = (message, analysis_msg)
                            else:
                                history[-1] = (message, bot_response)
                        else:
                            history[-1] = (message, bot_response)
                    else:
                        history[-1] = (message, bot_response)
            else:
                bot_response = "⚠️ Please start configuration first."
                history[-1] = (message, bot_response)
            
            yield history, "", gr.update(interactive=True)
        
        chat_input.submit(
            fn=on_chat_with_typing,
            inputs=[chat_input, chatbot],
            outputs=[chatbot, chat_input, send_btn]
        ).then(
            fn=refresh_questions_panel,
            inputs=[category_dropdown],
            outputs=[status_display, category_dropdown, questions_panel]
        )
        
        send_btn.click(
            fn=on_chat_with_typing,
            inputs=[chat_input, chatbot],
            outputs=[chatbot, chat_input, send_btn]
        ).then(
            fn=refresh_questions_panel,
            inputs=[category_dropdown],
            outputs=[status_display, category_dropdown, questions_panel]
        )
    
    return app


if __name__ == "__main__":
    logger.info("🚀 Starting Config-Copilot Interactive Agent")
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    app = create_gradio_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
