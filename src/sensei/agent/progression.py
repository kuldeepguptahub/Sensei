"""
Lesson progression logic for Sensei.

Handles parsing planner.md, advancing through modules/lessons,
calculating progress, and detecting milestones.
"""

import re
from typing import List, Dict, Any, Optional


def parse_planner(content: str) -> List[Dict[str, Any]]:
    """
    Parse planner.md into a structured list of modules and lessons.

    Uses flexible heuristics to detect:
    - Modules: lines starting with ### or ## containing "Module"
    - Lessons: lines starting with - or * under a module
    - Milestones: lines containing "milestone" (case-insensitive)
    - Projects: lines containing "project" (case-insensitive)

    Args:
        content: The raw planner.md content

    Returns:
        List of module dicts, each containing:
        - name: Module name
        - lessons: List of lesson dicts with "name" and "type" (lesson/milestone/project)
    """
    modules = []
    current_module = None

    for line in content.split("\n"):
        stripped = line.strip()

        # Detect module headers (### Module X: Name or ## Module X)
        if re.match(r"^#{2,3}\s+.*[Mm]odule", stripped):
            # Extract module name after the #
            module_name = re.sub(r"^#{2,3}\s+", "", stripped).strip()
            current_module = {"name": module_name, "lessons": []}
            modules.append(current_module)
            continue

        # If we're inside a module, look for lessons/milestones/projects
        if current_module is not None:
            # Detect list items (- or *)
            lesson_match = re.match(r"^[-*]\s+(.+)", stripped)
            if lesson_match:
                item_text = lesson_match.group(1).strip()

                # Classify the item
                item_lower = item_text.lower()
                if "milestone" in item_lower:
                    item_type = "milestone"
                elif "project" in item_lower:
                    item_type = "project"
                else:
                    item_type = "lesson"

                current_module["lessons"].append({
                    "name": item_text,
                    "type": item_type
                })

    return modules


def advance_lesson(state: Dict[str, Any], modules: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Advance to the next lesson in the course.

    If at the last lesson of a module, moves to the next module.
    If at the last module, marks course as completed.

    Args:
        state: Current state.json dict
        modules: Parsed planner modules

    Returns:
        Updated state dict
    """
    if not modules:
        return state

    current_module_idx = state.get("current_module", 0)
    current_lesson_idx = state.get("current_lesson", 0)

    # Validate current position
    if current_module_idx >= len(modules):
        state["status"] = "completed"
        return state

    current_module = modules[current_module_idx]
    lessons = current_module.get("lessons", [])

    # Advance to next lesson
    if current_lesson_idx < len(lessons) - 1:
        state["current_lesson"] = current_lesson_idx + 1
    elif current_module_idx < len(modules) - 1:
        # Move to next module, first lesson
        state["current_module"] = current_module_idx + 1
        state["current_lesson"] = 0
    else:
        # Last lesson of last module
        state["status"] = "completed"

    # Update progress
    state["progress"] = calculate_progress(state, modules)

    return state


def calculate_progress(state: Dict[str, Any], modules: List[Dict[str, Any]]) -> float:
    """
    Calculate overall progress as a float between 0.0 and 1.0.

    Based on position in the roadmap (modules and lessons completed).

    Args:
        state: Current state.json dict
        modules: Parsed planner modules

    Returns:
        Progress value between 0.0 and 1.0
    """
    if not modules:
        return 0.0

    current_module_idx = state.get("current_module", 0)
    current_lesson_idx = state.get("current_lesson", 0)

    # Count total lessons across all modules
    total_lessons = sum(len(m.get("lessons", [])) for m in modules)
    if total_lessons == 0:
        return 0.0

    # Count completed lessons (all lessons in prior modules + lessons in current module)
    completed_lessons = 0
    for i in range(current_module_idx):
        completed_lessons += len(modules[i].get("lessons", []))
    completed_lessons += current_lesson_idx

    return min(completed_lessons / total_lessons, 1.0)


def is_milestone_reached(state: Dict[str, Any], modules: List[Dict[str, Any]]) -> bool:
    """
    Check if the current position is at a milestone.

    Args:
        state: Current state.json dict
        modules: Parsed planner modules

    Returns:
        True if current lesson is a milestone
    """
    current_module_idx = state.get("current_module", 0)
    current_lesson_idx = state.get("current_lesson", 0)

    if current_module_idx >= len(modules):
        return False

    lessons = modules[current_module_idx].get("lessons", [])
    if current_lesson_idx >= len(lessons):
        return False

    return lessons[current_lesson_idx].get("type") == "milestone"


def get_current_lesson(state: Dict[str, Any], modules: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Get the current lesson dict from the parsed modules.

    Args:
        state: Current state.json dict
        modules: Parsed planner modules

    Returns:
        Current lesson dict with "name" and "type", or None if not found
    """
    current_module_idx = state.get("current_module", 0)
    current_lesson_idx = state.get("current_lesson", 0)

    if current_module_idx >= len(modules):
        return None

    lessons = modules[current_module_idx].get("lessons", [])
    if current_lesson_idx >= len(lessons):
        return None

    return lessons[current_lesson_idx]


def get_module_context(state: Dict[str, Any], modules: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Get the current module dict from the parsed modules.

    Args:
        state: Current state.json dict
        modules: Parsed planner modules

    Returns:
        Current module dict with "name" and "lessons", or None if not found
    """
    current_module_idx = state.get("current_module", 0)

    if current_module_idx >= len(modules):
        return None

    return modules[current_module_idx]
