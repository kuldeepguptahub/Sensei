"""
Competency evaluation for Sensei.

Handles generating evaluation prompts, parsing responses,
and updating competency scores.
"""

import re
import json
from typing import Dict, Any, Optional


def build_evaluation_prompt(lesson_topic: str, course_topic: str) -> str:
    """
    Build a prompt for the LLM to generate quiz/exercise questions.

    Args:
        lesson_topic: The topic of the current lesson
        course_topic: The overall course topic

    Returns:
        A prompt string for the LLM
    """
    return f"""Generate a short evaluation for the learner.

Course topic: {course_topic}
Lesson topic: {lesson_topic}

Create 2-3 questions or exercises that test understanding of this lesson.
Mix question types: concept checks, short code examples, or practical applications.

Format your response as:

**Evaluation**
Q1: [question]
Q2: [question]
Q3: [question]

Provide clear, specific questions that assess real understanding.
"""


def build_grading_prompt(lesson_topic: str, questions: str, learner_response: str) -> str:
    """
    Build a prompt for the LLM to evaluate a learner's response.

    Args:
        lesson_topic: The topic being evaluated
        questions: The questions that were asked
        learner_response: The learner's answer

    Returns:
        A prompt string for the LLM to grade the response
    """
    return f"""Grade the learner's response to the following evaluation.

Lesson topic: {lesson_topic}

Questions:
{questions}

Learner's response:
{learner_response}

Evaluate the response and provide:
1. A score from 0-10 (where 7+ is passing)
2. Brief feedback on what was correct and what needs improvement
3. Whether the learner passed (score >= 7)

Format your response as:
Score: [0-10]
Passed: [true/false]
Feedback: [your feedback]
"""


def parse_evaluation_response(response: str) -> Dict[str, Any]:
    """
    Parse the LLM's grading response into structured data.

    Args:
        response: The LLM's grading response

    Returns:
        Dict with "score" (int), "passed" (bool), "feedback" (str)
    """
    result = {"score": 0, "passed": False, "feedback": response}

    # Extract score
    score_match = re.search(r"Score:\s*(\d+)", response, re.IGNORECASE)
    if score_match:
        result["score"] = int(score_match.group(1))

    # Extract passed
    passed_match = re.search(r"Passed:\s*(true|false)", response, re.IGNORECASE)
    if passed_match:
        result["passed"] = passed_match.group(1).lower() == "true"

    # Extract feedback
    feedback_match = re.search(r"Feedback:\s*(.+)", response, re.IGNORECASE | re.DOTALL)
    if feedback_match:
        result["feedback"] = feedback_match.group(1).strip()

    # Fallback: if score was provided but passed wasn't, derive from score
    if score_match and not passed_match:
        result["passed"] = result["score"] >= 7

    return result


def update_competency(state: Dict[str, Any], lesson_key: str, score: int) -> Dict[str, Any]:
    """
    Update the competency_index in state with a new score.

    Args:
        state: Current state.json dict
        lesson_key: Key identifying the lesson (e.g., "module_0.lesson_0")
        score: Score from 0-10

    Returns:
        Updated state dict
    """
    if "competency_index" not in state:
        state["competency_index"] = {}

    state["competency_index"][lesson_key] = {
        "score": score,
        "passed": score >= 7
    }

    return state


def build_competency_summary(state: Dict[str, Any]) -> str:
    """
    Build a human-readable summary of competency scores.

    Args:
        state: Current state.json dict

    Returns:
        Formatted string summarizing competency
    """
    competency = state.get("competency_index", {})
    if not competency:
        return "No evaluations completed yet."

    lines = ["**Competency Summary**\n"]
    for lesson_key, data in sorted(competency.items()):
        score = data.get("score", 0)
        passed = "PASS" if data.get("passed", False) else "NEEDS REVIEW"
        lines.append(f"- {lesson_key}: {score}/10 [{passed}]")

    return "\n".join(lines)
