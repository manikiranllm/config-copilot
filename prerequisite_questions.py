"""
Prerequisite Questions Module - Ask discovery questions before configuration
WITH SPECIFIC ORACLE FUSION TERMINOLOGY
"""

import json
import logging
from typing import Dict, List, Optional
from llm_wrapper import call_llm_api_async

logger = logging.getLogger(__name__)


# HR/Payroll prerequisite questions - ORACLE FUSION SPECIFIC WITH DETAILED COMPONENTS
HR_PAYROLL_PREREQUISITES = {
    "Enterprise Structure": [
        {
            "id": "prereq_es_001",
            "question": "Have you already completed your Enterprise Structure setup in Oracle Fusion? Specifically, do you have your Legal Entities, Business Units, and Legal Employers defined?",
            "category": "Enterprise Structure",
            "required": True,
            "type": "text",
            "hint": "We need to know if you have the foundational structures in place or if we need to configure them as part of this implementation",
            "oracle_objects": ["Legal Entity", "Business Unit", "Legal Employer"]
        },
        {
            "id": "prereq_es_002",
            "question": "What is your Organization Hierarchy structure? Do you have your Department Tree, Cost Center Hierarchy, and Reporting Organizations defined?",
            "category": "Enterprise Structure",
            "required": True,
            "type": "text",
            "hint": "This determines how employees are organized and how financials roll up",
            "oracle_objects": ["Organization Hierarchy", "Department Tree", "Cost Center", "Reporting Organization"]
        }
    ],
    "Calendars & Time": [
        {
            "id": "prereq_cal_001",
            "question": "Have you set up your Payroll Calendars and HR Processing Calendars? What are your pay frequencies - Weekly, Bi-weekly, Semi-monthly, or Monthly?",
            "category": "Calendars & Time",
            "required": True,
            "type": "text",
            "hint": "Each pay frequency needs its own Payroll Calendar with defined Pay Periods",
            "oracle_objects": ["Payroll Calendar", "HR Processing Calendar", "Pay Period", "Processing Cycle"]
        },
        {
            "id": "prereq_cal_002",
            "question": "What Work Schedules do you need configured? Do you use standard 8-hour days, Shift Patterns, or Flexible Work Schedules?",
            "category": "Calendars & Time",
            "required": True,
            "type": "text",
            "hint": "This affects time tracking, absence management, and overtime calculations",
            "oracle_objects": ["Work Schedule", "Shift Pattern", "Time Entry", "Standard Hours"]
        }
    ],
    "Workforce Structures": [
        {
            "id": "prereq_ws_001",
            "question": "How is your Job Catalog structured? Do you have Job Families, Jobs, and Positions defined, or are you using a position-less HR model?",
            "category": "Workforce Structures",
            "required": True,
            "type": "text",
            "hint": "This is fundamental to how you organize and manage your workforce in Oracle HCM",
            "oracle_objects": ["Job Catalog", "Job Family", "Job", "Position", "Position Hierarchy"]
        },
        {
            "id": "prereq_ws_002",
            "question": "What Grade Ladders and Salary Ranges do you need? Do you have defined Grade Structures with salary steps, or market-based pay ranges?",
            "category": "Workforce Structures",
            "required": True,
            "type": "text",
            "hint": "This drives compensation decisions and pay progression in your system",
            "oracle_objects": ["Grade Ladder", "Grade", "Salary Range", "Pay Scale", "Compensation Structure"]
        }
    ],
    "Payroll Configuration": [
        {
            "id": "prereq_pay_001",
            "question": "What Payroll Elements do you need configured? Specifically, what are your standard Earnings (Salary, Hourly, Overtime), Deductions (401k, Health Insurance), and Tax Withholdings?",
            "category": "Payroll Configuration",
            "required": True,
            "type": "text",
            "hint": "Each element needs to be set up with calculation rules and costing allocations",
            "oracle_objects": ["Element", "Earnings Element", "Deduction Element", "Tax Element", "Element Eligibility"]
        },
        {
            "id": "prereq_pay_002",
            "question": "Do you have complex Payroll Rules? For example, union differentials, shift premiums, tax overrides, or special calculation formulas?",
            "category": "Payroll Configuration",
            "required": True,
            "type": "text",
            "hint": "These require Formula setup and may need custom Fast Formulas",
            "oracle_objects": ["Fast Formula", "Element Input Values", "Calculation Rule", "Balance Feeds"]
        }
    ],
    "Security & Access": [
        {
            "id": "prereq_sec_001",
            "question": "What Data Security Policies do you need? Do managers need access only to their direct reports, or do you have more complex security requirements?",
            "category": "Security & Access",
            "required": True,
            "type": "text",
            "hint": "This controls who can see and edit employee data in Oracle HCM",
            "oracle_objects": ["Data Security Policy", "HCM Group", "Security Profile", "Role-Based Access"]
        }
    ]
}


class PrerequisiteManager:
    """
    Manages prerequisite questions before main configuration flow
    """
    
    def __init__(self):
        self.all_prerequisites = HR_PAYROLL_PREREQUISITES
        self.state = {
            "phase": "not_started",  # not_started -> asking -> completed
            "questions": [],  # Filtered questions based on intent
            "answers": {},  # question_id -> answer
            "current_category": None,
            "completed_categories": []
        }
    
    async def initialize_prerequisites(self, intent_tags: List[str], initial_prompt: str) -> Dict:
        """
        Initialize prerequisite questions based on intent
        
        Returns:
            {
                "questions": [...],
                "initial_message": "...",
                "required_count": 10
            }
        """
        
        try:
            logger.info(f"📋 Initializing prerequisites for tags: {intent_tags}")
            
            # Check if HR/Payroll related
            hr_payroll_tags = ["core hr", "payroll", "human capital management", "hcm", 
                              "workforce", "compensation", "benefits", "time and labor"]
            
            is_hr_payroll = any(tag.lower() in [t.lower() for t in hr_payroll_tags] for tag in intent_tags)
            
            if not is_hr_payroll:
                # Not HR/Payroll, skip prerequisites
                logger.info("   ℹ️ Not HR/Payroll implementation, skipping prerequisites")
                self.state["phase"] = "completed"
                return {
                    "questions": [],
                    "initial_message": "Starting configuration directly...",
                    "required_count": 0
                }
            
            # Filter questions based on intent analysis
            selected_questions = await self._select_relevant_questions(initial_prompt, intent_tags)
            
            self.state["questions"] = selected_questions
            self.state["phase"] = "asking"
            self.state["current_category"] = selected_questions[0]["category"] if selected_questions else None
            
            # Generate initial message
            initial_message = self._generate_initial_prerequisites_message(selected_questions)
            
            required_count = sum(1 for q in selected_questions if q.get("required", False))
            
            logger.info(f"   ✅ Prepared {len(selected_questions)} questions ({required_count} required)")
            
            return {
                "questions": selected_questions,
                "initial_message": initial_message,
                "required_count": required_count
            }
            
        except Exception as e:
            logger.error(f"❌ Error initializing prerequisites: {e}")
            self.state["phase"] = "completed"
            return {
                "questions": [],
                "initial_message": "Proceeding with configuration...",
                "required_count": 0
            }
    
    async def _select_relevant_questions(self, initial_prompt: str, intent_tags: List[str]) -> List[Dict]:
        """
        Select relevant prerequisite questions - simplified to always use core 5
        """
        
        # Flatten all questions
        all_questions = []
        for category, questions in self.all_prerequisites.items():
            all_questions.extend(questions)
        
        # For HR/Payroll, always use all 5 core questions (6th is optional)
        # These are already optimized and cover all essential areas
        logger.info(f"   📊 Using {len(all_questions)} core prerequisite questions")
        
        return all_questions
    
    def _generate_initial_prerequisites_message(self, questions: List[Dict]) -> str:
        """Generate initial message explaining prerequisites"""
        
        categories = {}
        for q in questions:
            cat = q["category"]
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1
        
        category_summary = "\n".join([f"   • **{cat}**: {count} questions" for cat, count in categories.items()])
        
        # Get oracle objects from first question if available
        oracle_hint = ""
        if "oracle_objects" in questions[0]:
            objects = ", ".join(questions[0]["oracle_objects"])
            oracle_hint = f"\n\n💡 *We'll be discussing: {objects}*"
        
        return f"""🎯 **Before we configure your system, I need to understand your Oracle Fusion prerequisites.**

I've prepared **{len(questions)} prerequisite questions** that will help me configure your Oracle ERP optimally:

{category_summary}

📋 **How this works:**
- I'll ask specific questions about Oracle Fusion components
- Answer based on what you have already configured
- If something isn't set up yet, just let me know
- Your answers will help me pre-configure the right modules

Let's start with **{questions[0]['category']}**!{oracle_hint}

{questions[0]['question']}"""
    
    async def process_answer(self, user_message: str) -> Dict:
        """
        Process user's answer to current prerequisite question
        
        Returns:
            {
                "next_question": "...",
                "response": "...",
                "progress": "3/15",
                "is_complete": False
            }
        """
        
        try:
            if self.state["phase"] != "asking":
                return {
                    "is_complete": True,
                    "response": "Prerequisites already completed!"
                }
            
            # Find current question
            answered_count = len(self.state["answers"])
            
            if answered_count >= len(self.state["questions"]):
                # All questions answered
                self.state["phase"] = "completed"
                return {
                    "is_complete": True,
                    "response": self._generate_completion_message(),
                    "progress": f"{answered_count}/{len(self.state['questions'])}"
                }
            
            current_question = self.state["questions"][answered_count]
            
            # Store answer
            self.state["answers"][current_question["id"]] = {
                "question": current_question["question"],
                "answer": user_message,
                "category": current_question["category"]
            }
            
            # Check if category changed
            category_changed = (
                self.state["current_category"] != current_question["category"]
                and answered_count > 0
            )
            
            if category_changed:
                self.state["completed_categories"].append(self.state["current_category"])
                self.state["current_category"] = current_question["category"]
            
            # Get next question
            next_index = answered_count + 1
            
            if next_index >= len(self.state["questions"]):
                # This was the last question
                self.state["phase"] = "completed"
                return {
                    "is_complete": True,
                    "response": self._generate_completion_message(),
                    "progress": f"{next_index}/{len(self.state['questions'])}"
                }
            
            next_question = self.state["questions"][next_index]
            
            # Generate response with next question
            response = await self._generate_followup_response(
                current_question,
                next_question,
                user_message,
                category_changed
            )
            
            return {
                "is_complete": False,
                "response": response,
                "next_question": next_question["question"],
                "progress": f"{next_index}/{len(self.state['questions'])}",
                "category": next_question["category"]
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing answer: {e}")
            return {
                "is_complete": False,
                "response": "I encountered an error. Could you please repeat that?",
                "progress": f"{answered_count}/{len(self.state['questions'])}"
            }
    
    async def _generate_followup_response(
        self,
        current_question: Dict,
        next_question: Dict,
        user_answer: str,
        category_changed: bool
    ) -> str:
        """Generate contextual response acknowledging answer and asking next question"""
        
        system_prompt = f"""You are an experienced Oracle Fusion consultant conducting a discovery interview.

**YOUR TASK:**
1. Briefly acknowledge the user's answer (1 sentence)
2. If category changed, mention we're moving to a new area with Oracle components
3. Ask the next question with specific Oracle Fusion terminology
4. Include the specific Oracle objects/components in the question

Keep it conversational, professional, and under 100 words.
Demonstrate expertise by using proper Oracle terminology.

Return ONLY the response text, no JSON, no markdown."""

        # Include Oracle objects in the context
        oracle_context = ""
        if "oracle_objects" in next_question:
            oracle_context = f"\nOracle Components: {', '.join(next_question['oracle_objects'])}"
        
        user_prompt = f"""**USER JUST ANSWERED:**
Q: {current_question['question']}
A: {user_answer}

**NEXT QUESTION:**
Category: {next_question['category']}
Q: {next_question['question']}{oracle_context}

Category changed: {category_changed}

Progress: {len(self.state['answers']) + 1}/{len(self.state['questions'])}

Generate your response with specific Oracle Fusion terminology:"""

        try:
            response = await call_llm_api_async(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error generating followup: {e}")
            
            # Fallback response with Oracle terminology
            oracle_hint = ""
            if "oracle_objects" in next_question:
                objects = ", ".join(next_question['oracle_objects'])
                oracle_hint = f" We'll be discussing: {objects}."
            
            if category_changed:
                return f"""Got it, thanks! 

Now let's move to **{next_question['category']}**.{oracle_hint}

{next_question['question']}"""
            else:
                return f"""Thanks! 

{next_question['question']}"""
    
    def _generate_completion_message(self) -> str:
        """Generate message when all prerequisites are complete"""
        
        return f"""✅ **Excellent! All prerequisite questions completed.**

📊 **Summary:**
- Answered {len(self.state['answers'])} questions
- Covered {len(set(a['category'] for a in self.state['answers'].values()))} categories

🚀 **Now I'll use this information to:**
1. Generate your company's baseline configuration
2. Fetch relevant Oracle ERP questions
3. Pre-fill answers based on what you've told me

This will take about 2-3 minutes. Please wait...

⏳ Starting configuration analysis..."""
    
    def get_answers_summary(self) -> Dict:
        """Get summary of all collected answers"""
        
        return {
            "total_questions": len(self.state["questions"]),
            "answered": len(self.state["answers"]),
            "answers": self.state["answers"],
            "is_complete": self.state["phase"] == "completed"
        }
    
    def is_complete(self) -> bool:
        """Check if prerequisites are complete"""
        return self.state["phase"] == "completed"
