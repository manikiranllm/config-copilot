#!/usr/bin/env python
"""
Phase Extractors Package - Simplified Version
"""

from .phase1_extractor import create_phase1_extractor
from .phase2_extractor import create_phase2_extractor  
from .phase3_extractor import create_phase3_extractor
from .phase4_extractor import create_phase4_extractor
from .phase5_extractor import create_phase5_extractor
from .phase6_extractor import create_phase6_extractor
from .phase7_extractor import create_phase7_extractor
from .phase8_extractor import create_phase8_extractor
from .phase9_extractor import create_phase9_extractor

# Registry of all phase extractors
PHASE_EXTRACTORS = {
    1: create_phase1_extractor,
    2: create_phase2_extractor,
    3: create_phase3_extractor,
    4: create_phase4_extractor,
    5: create_phase5_extractor,
    6: create_phase6_extractor,
    7: create_phase7_extractor,
    8: create_phase8_extractor,
    9: create_phase9_extractor
}

def get_phase_extractor(phase_num: int):
    """Get extractor for specific phase"""
    if phase_num not in PHASE_EXTRACTORS:
        raise ValueError(f"Phase {phase_num} extractor not implemented yet")
    
    return PHASE_EXTRACTORS[phase_num]()

def get_available_phases():
    """Get list of available phase numbers"""
    return list(PHASE_EXTRACTORS.keys())

__all__ = [
    'get_phase_extractor',
    'get_available_phases',
]
