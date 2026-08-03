"""
Agent package for Sensei.

This package provides the core agent functionality.
"""

from .runner import run, load_instructions
from .registry import register, get_skill, list_skills

__all__ = ['run', 'load_instructions', 'register', 'get_skill', 'list_skills']