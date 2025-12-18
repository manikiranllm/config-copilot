#!/usr/bin/env python
"""
Simple test to check if selected category filtering works
"""

categories = {
    "Payroll": [{"questions": "Q1"}, {"questions": "Q2"}],
    "Benefits": [{"questions": "Q3"}, {"questions": "Q4"}],
    "HR": [{"questions": "Q5"}]
}

selected = "Payroll"

print(f"Selected: {selected}")
print(f"Questions: {categories.get(selected, [])}")
print(f"All categories: {list(categories.keys())}")
