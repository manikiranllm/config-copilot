def create_questions_html_filtered(agent, selected_category):
    """Helper to create filtered HTML"""
    if not agent or not agent.state.get("categories"):
        return ""
    
    categories = agent.state["categories"]
    
    # Filter categories
    if selected_category and selected_category != "All" and selected_category in categories:
        categories_to_show = {selected_category: categories[selected_category]}
    else:
        categories_to_show = categories
    
    html = "<div style='max-height: 600px; overflow-y: auto;'>"
    
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
    
    html += "</div>"
    return html
