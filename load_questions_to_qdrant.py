#!/usr/bin/env python
"""
Helper script to load Oracle questionnaire into Qdrant
This is a TEMPLATE - you need to provide your own questions data
"""

import os
import json
import uuid
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

load_dotenv()

def load_questions_to_qdrant():
    """
    Load questions into Qdrant
    
    IMPORTANT: You need to provide your own questions data.
    Replace the sample_questions below with your actual questions.
    """
    
    print("=" * 60)
    print("📤 Loading Oracle Questions to Qdrant")
    print("=" * 60)
    
    # Configuration
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection_name = os.getenv("QDRANT_COLLECTION", "oracle_questions")
    
    # SAMPLE QUESTIONS - Replace with your actual data
    sample_questions = [
        {
            "id": "Q001",
            "categoryID": "Payroll_Configuration",
            "questions": "What is the pay frequency for employees?",
            "mandatoryField": "Pay Frequency",
            "isrequired": True,
            "tags": ["payroll", "hr"]
        },
        {
            "id": "Q002",
            "categoryID": "HR_Management",
            "questions": "What is the probation period for new hires?",
            "mandatoryField": "Probation Period",
            "isrequired": True,
            "tags": ["hr", "hcm"]
        },
        {
            "id": "Q003",
            "categoryID": "General_Ledger",
            "questions": "What is the fiscal year start date?",
            "mandatoryField": "Fiscal Year Start",
            "isrequired": True,
            "tags": ["gl", "finance"]
        },
        {
            "id": "Q004",
            "categoryID": "Accounts_Payable",
            "questions": "What is the standard payment term for vendors?",
            "mandatoryField": "Payment Terms",
            "isrequired": True,
            "tags": ["payables", "finance"]
        },
        {
            "id": "Q005",
            "categoryID": "Accounts_Receivable",
            "questions": "What is the credit limit for new customers?",
            "mandatoryField": "Credit Limit",
            "isrequired": False,
            "tags": ["receivables", "finance"]
        }
    ]
    
    print("\n⚠️  IMPORTANT: Using sample questions!")
    print("   You need to replace 'sample_questions' in this script")
    print("   with your actual Oracle questions data.")
    print(f"\n📁 Sample questions: {len(sample_questions)}")
    
    response = input("\nContinue with sample data? (y/N): ")
    if response.lower() != 'y':
        print("Aborted. Please update the script with your questions.")
        return False
    
    questions = sample_questions
    
    # Connect to Qdrant
    print(f"\n🔌 Connecting to Qdrant: {qdrant_url}")
    try:
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        print("✅ Connected!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Check if collection exists, create if not
    print(f"\n📊 Checking collection: {collection_name}")
    try:
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if collection_name not in collection_names:
            print(f"   Creating collection '{collection_name}'...")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            print("   ✅ Collection created!")
        else:
            print(f"   ✅ Collection exists")
            
            # Ask if user wants to delete existing data
            response = input(f"\n⚠️ Delete existing data in '{collection_name}'? (y/N): ")
            if response.lower() == 'y':
                client.delete_collection(collection_name)
                print(f"   🗑️ Deleted existing collection")
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                print(f"   ✅ Recreated collection")
    except Exception as e:
        print(f"❌ Error with collection: {e}")
        return False
    
    # Process and upload questions
    print(f"\n📤 Uploading {len(questions)} questions...")
    
    points = []
    for idx, q in enumerate(questions, 1):
        # Generate a dummy vector (you might want to use actual embeddings)
        dummy_vector = [0.0] * 384
        
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=dummy_vector,
            payload={
                "id": q.get("id", f"Q{idx:03d}"),
                "categoryID": q.get("categoryID", "General"),
                "questions": q.get("questions", ""),
                "mandatoryField": q.get("mandatoryField", ""),
                "isrequired": q.get("isrequired", False),
                "tags": q.get("tags", ["general"])
            }
        )
        points.append(point)
    
    # Upload
    try:
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        print(f"\n✅ Successfully uploaded {len(points)} questions!")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False
    
    # Verify
    print(f"\n✔️ Verifying upload...")
    try:
        info = client.get_collection(collection_name)
        print(f"   Total points in collection: {info.points_count}")
    except Exception as e:
        print(f"⚠️ Could not verify: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Upload complete! Run test_qdrant.py to verify.")
    print("\n⚠️  Remember to replace sample questions with your actual data!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    load_questions_to_qdrant()
