#!/usr/bin/env python
"""
Helper to create questionnaire tabs/accordions dynamically
"""

import gradio as gr
from typing import Dict, List


def create_category_tab(category_name: str, category_questions: List[Dict]) -> List:
    """
    Create UI components for a single category
    Returns list of textbox components
    """
    components = []
    
    gr.Markdown(f"### {category_name.replace('_', ' ')}")
    gr.Markdown(f"*{len(category_questions)} questions in this category*")
    gr.Markdown("---")
    
    for q in category_questions:
        q_id = q["id"]
        question_text = q.get("questions", "")
        mandatory_field = q.get("mandatoryField", "")
        answer = q.get("answer", "")
        is_required = q.get("isrequired", False)
        
        # Build label
        req_icon = "✅" if is_required else "⚪"
        label = f"{req_icon} Q{q_id}: {mandatory_field}"
        
        # Create text input
        textbox = gr.Textbox(
            label=label,
            value=answer if answer else "",
            placeholder="",
            lines=1,
            interactive=True,
            info=question_text if question_text else None
        )
        
        components.append(textbox)
    
    return components


def build_questionnaire_tabs_html(filled_questions: List[Dict]) -> str:
    """
    Build HTML representation of questionnaire with tabs
    """
    
    # Group by category
    categories = {}
    for q in filled_questions:
        category = q.get("categoryID", "General")
        if category not in categories:
            categories[category] = []
        categories[category].append(q)
    
    # Start HTML
    html_parts = []
    
    html_parts.append("""
    <style>
        .questionnaire-container {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .category-content { 
            padding: 20px; 
            border: 1px solid #ddd; 
            border-radius: 8px;
            margin: 20px 0;
            background: white;
        }
        .question-item {
            padding: 15px;
            margin: 15px 0;
            border-left: 4px solid #4CAF50;
            background: #f9f9f9;
            border-radius: 4px;
        }
        .question-label { 
            font-weight: bold; 
            color: #333;
            margin-bottom: 8px;
            display: block;
        }
        .question-text {
            color: #666;
            font-size: 0.95em;
            margin: 8px 0;
            font-style: italic;
        }
        .answer-field {
            width: 100%;
            padding: 10px;
            margin-top: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            box-sizing: border-box;
        }
        .answer-field:focus {
            outline: none;
            border-color: #4CAF50;
        }
        .required { color: #4CAF50; font-weight: bold; }
        .optional { color: #999; }
        .category-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .stats {
            background: #f0f0f0;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
    </style>
    
    <div class="questionnaire-container">
        <h2 style="color: #333;">📋 Oracle Fusion ERP System Questionnaire</h2>
    """)
    
    html_parts.append(f"""
        <div class="stats">
            <strong>Total Questions:</strong> {len(filled_questions)} across {len(categories)} categories
            <br>
            <em>Scroll through each category below. Fields are pre-filled where data is available.</em>
        </div>
    """)
    
    # Add each category
    for category_name in sorted(categories.keys()):
        category_questions = categories[category_name]
        
        html_parts.append(f"""
        <div class="category-content">
            <div class="category-header">
                <h3 style="margin: 0; color: white;">📂 {category_name.replace('_', ' ')}</h3>
                <p style="margin: 5px 0 0 0; color: rgba(255,255,255,0.9);">{len(category_questions)} questions</p>
            </div>
        """)
        
        for q in category_questions:
            q_id = q["id"]
            question_text = q.get("questions", "")
            mandatory_field = q.get("mandatoryField", "")
            answer = q.get("answer", "")
            is_required = q.get("isrequired", False)
            
            req_class = "required" if is_required else "optional"
            req_text = "✅ Required" if is_required else "⚪ Optional"
            
            # Escape HTML in values
            answer_escaped = answer.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;') if answer else ""
            question_escaped = question_text.replace('<', '&lt;').replace('>', '&gt;') if question_text else ""
            field_escaped = mandatory_field.replace('<', '&lt;').replace('>', '&gt;') if mandatory_field else ""
            
            html_parts.append(f"""
            <div class="question-item">
                <div class="question-label">
                    <span class="{req_class}">Q{q_id}: {field_escaped}</span>
                    <span style="float: right; font-size: 0.85em; font-weight: normal;">{req_text}</span>
                </div>
            """)
            
            if question_escaped:
                html_parts.append(f'<div class="question-text">{question_escaped}</div>')
            
            html_parts.append(f'<input type="text" class="answer-field" value="{answer_escaped}" placeholder="Enter answer here..." readonly />')
            html_parts.append('</div>')
        
        html_parts.append('</div>')
    
    html_parts.append('</div>')
    
    return ''.join(html_parts)
