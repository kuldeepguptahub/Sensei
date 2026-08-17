"""
Context management for Sensei.

Handles compressing conversation history into context.md summaries
and building resumption prompts for session continuity.
"""

from typing import Dict, Any, List


def compress_history(history: List[Dict[str, str]], course_name: str) -> str:
    """
    Compress conversation history into a compact working memory summary.

    Uses the LLM to summarize old messages into key facts, decisions,
    learner profile, and progress notes.

    Args:
        history: List of message dicts {"role": ..., "content": ...} to compress
        course_name: Name of the course (for context)

    Returns:
        Summary string to be written to context.md
    """
    from .runner import run_simple

    # Format the conversation for summarization
    conversation_text = ""
    for msg in history:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        conversation_text += f"{role}: {content}\n\n"

    summarization_prompt = f"""Summarize the following teaching conversation for course "{course_name}".

Create a concise working memory summary that includes:
1. Learner profile (knowledge level, learning style, goals)
2. Key topics covered so far
3. Learner's demonstrated strengths
4. Areas that need reinforcement
5. Any adjustments made to the learning plan
6. Current focus and next steps

Conversation:
{conversation_text}

Provide a structured summary (under 500 words) that would help resume this teaching session later. Use markdown formatting."""

    summary = run_simple(summarization_prompt)
    return summary


def build_resumption_context(context_md: str, state: Dict[str, Any]) -> str:
    """
    Format context.md and state into an injectable prompt block.

    Used when resuming a course that has existing context.

    Args:
        context_md: Content of context.md
        state: Current state.json dict

    Returns:
        Formatted string to prepend to the first prompt
    """
    current_module = state.get("current_module", 0)
    current_lesson = state.get("current_lesson", 0)
    progress = state.get("progress", 0.0)
    status = state.get("status", "active")
    competency = state.get("competency_index", {})

    # Build competency summary
    competency_lines = []
    for lesson_key, data in sorted(competency.items()):
        score = data.get("score", 0)
        passed = "PASS" if data.get("passed", False) else "NEEDS REVIEW"
        competency_lines.append(f"  - {lesson_key}: {score}/10 [{passed}]")
    competency_text = "\n".join(competency_lines) if competency_lines else "  No evaluations yet"

    context_block = f"""=== PREVIOUS SESSION CONTEXT ===

{context_md}

=== CURRENT POSITION ===
- Module: {current_module}
- Lesson: {current_lesson}
- Progress: {progress:.0%}
- Status: {status}

=== COMPETENCY SCORES ===
{competency_text}

=== INSTRUCTIONS ===
Continue teaching from where we left off. Briefly acknowledge what was covered before, then continue with the current lesson.
"""

    return context_block
