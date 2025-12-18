"""
Question Retriever - Fetch questions from your RAG API
"""

import os
import requests
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class QuestionRetriever:
    def __init__(self):
        self.api_url = os.getenv(
            "QUESTION_API_URL", 
            "https://runpodroute.preprod.opkeyone.com/GenericRAGDev/api/v1/query/search"
        )
        self.collection_name = os.getenv("QUESTION_COLLECTION", "questionnaire_items")
        logger.info(f"✅ Question retriever initialized: {self.api_url}")
    
    def fetch_questions_by_tags(self, tags: List[str]) -> List[Dict]:
        """
        Fetch questions from your RAG API filtered by domain tags
        
        Args:
            tags: List of domain tags like ["core hr", "payroll", "benefits"]
        
        Returns:
            List of question objects
        """
        try:
            logger.info(f"🔍 Fetching questions for tags: {tags}")
            
            all_questions = []
            question_texts_seen = set()  # To avoid duplicates based on text
            
            # Fetch questions for each tag
            for tag in tags:
                # Convert to lowercase for API
                tag_lower = tag.lower()
                
                payload = {
                    "query": "a",  # Broad query to get many results
                    "domain_name": self.collection_name,
                    "limit": 100,  # Get up to 100 questions per tag
                    "threshold": 0.1,
                    "metadata_filters": {
                        "domain": tag_lower  # Use lowercase!
                    },
                    "vector_name": "tag_vector"
                }
                
                try:
                    response = requests.post(
                        self.api_url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    results = data.get("results", [])
                    
                    logger.info(f"   Found {len(results)} questions for tag '{tag_lower}'")
                    
                    # Convert to our format
                    for idx, item in enumerate(results):
                        question_text = item.get("text", "")
                        
                        # Avoid duplicates based on question text
                        if question_text in question_texts_seen:
                            continue
                        question_texts_seen.add(question_text)
                        
                        metadata = item.get("metadata", {})
                        
                        # Generate unique ID based on domain and index
                        question_id = f"{tag_lower.replace(' ', '_')}_{len(all_questions) + 1}"
                        
                        question_obj = {
                            "id": question_id,
                            "categoryID": metadata.get("pillar", tag_lower),
                            "questions": question_text,
                            "mandatoryField": question_text[:50] + "..." if len(question_text) > 50 else question_text,
                            "isrequired": False,  # Default
                            "tags": [tag_lower],
                            "domain": metadata.get("domain", tag_lower),
                            "pillar": metadata.get("pillar", ""),
                            "facet": metadata.get("facet", ""),
                            "composite_tag": metadata.get("composite_tag", ""),
                            "score": item.get("score", 0)
                        }
                        all_questions.append(question_obj)
                        
                except requests.RequestException as e:
                    logger.error(f"   ❌ API error for tag '{tag_lower}': {e}")
                    continue
            
            logger.info(f"✅ Retrieved {len(all_questions)} unique questions across all tags")
            return all_questions
            
        except Exception as e:
            logger.error(f"❌ Question fetch error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def get_all_available_tags(self) -> List[str]:
        """
        Get all available domain tags (lowercase as they are in the database)
        """
        return [
            "core hr",
            "payroll",
            "benefits",
            "compensation",
            "absence management",
            "time and labor",
            "talent management",
            "recruiting",
            "onboarding",
            "learning"
        ]
    
    def test_connection(self) -> bool:
        """Test if the API is accessible"""
        try:
            payload = {
                "query": "test",
                "domain_name": self.collection_name,
                "limit": 1,
                "threshold": 0.1,
                "vector_name": "tag_vector"
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ API connection successful, found {data.get('total_results', 0)} results")
            return True
            
        except Exception as e:
            logger.error(f"❌ API connection failed: {e}")
            return False
