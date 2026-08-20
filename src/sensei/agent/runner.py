"""
Agent runner for Sensei.

This module is responsible for:
- Loading agent instructions
- Registering skills
- Invoking the gateway
- Executing tool calls from structured API responses
- Returning responses
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Generator
from ..gateway.client import generate, generate_stream
from .tools import (
    MAX_TOOL_CALLS,
    MAX_RETRIES,
    get_tool_schemas_for_prompt,
)
from .registry import get_skill
from ..logger import log_tool, log_error


def load_instructions() -> str:
    """
    Load the agent instructions from instructions.md.

    Returns:
        The instructions text
    """
    instructions_path = Path(__file__).parent / "instructions.md"
    return instructions_path.read_text(encoding="utf-8")


def execute_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool by name with the given arguments.

    Args:
        name: The tool/skill name to execute
        args: The arguments to pass to the tool

    Returns:
        Dict with 'success' key and either 'data' or 'error' key
    """
    try:
        skill = get_skill(name)
    except KeyError:
        return {
            "success": False,
            "error": (
                f"Unknown tool: '{name}'. "
                f"You can only use tools that are defined in your available tools list. "
                f"Do NOT invent or hallucinate tool names. "
                f"Available tools: create_workspace, list_courses, delete_course, rename_course, "
                f"read_artifact, write_artifact, list_artifacts, workspace_exists, "
                f"save_upload, read_upload, list_uploads, update_state. "
                f"For everything else (teaching, explaining, asking questions), just respond with text."
            )
        }

    try:
        result = skill(**args)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def format_tool_result(tool_name: str, tool_args: Dict[str, Any], result: Dict[str, Any],
                       mode: str = "new_course", context: Optional[Dict[str, Any]] = None) -> str:
    """
    Format a tool execution result for the conversation.

    Includes a next-step hint so the model knows what to do after a tool call.

    Args:
        tool_name: Name of the tool that was called
        tool_args: Arguments passed to the tool
        result: The tool execution result dict
        mode: Session mode — "new_course" or "resume_course"
        context: Current course context with current_module, current_lesson, progress

    Returns:
        Formatted string for the conversation
    """
    if not result["success"]:
        error_msg = result["error"]
        hint = _error_hint(tool_name, tool_args, error_msg)
        base = f"<tool_result>\nsuccess: false\nerror: {error_msg}\n</tool_result>"
        if hint:
            base += f"\n\n{hint}"
        return base

    data = result.get("data")
    base = f"<tool_result>\nsuccess: true"
    if data is not None:
        base += f"\ndata: {data}"
    base += "\n</tool_result>"

    # Add next-step hints based on what the tool just did
    hint = _next_step_hint(tool_name, tool_args, mode, context)
    if hint:
        base += f"\n\n{hint}"

    return base


def _error_hint(tool_name: str, args: Dict[str, Any], error: str) -> str:
    """
    Return a hint when a tool call fails.

    Args:
        tool_name: Name of the tool that was called
        args: Arguments passed to the tool
        error: The error message

    Returns:
        Hint string, or empty string if no hint needed
    """
    if tool_name == "update_state":
        if "missing required field" in error.lower():
            return (
                "Your state_json is missing required fields. "
                "Always include: current_module (int), current_lesson (int), "
                "progress (float 0-1), status (string), last_accessed (ISO timestamp), "
                "last_updated (ISO timestamp). "
                "Example: {\"current_module\":0,\"current_lesson\":0,\"progress\":0.0,\"status\":\"active\","
                "\"last_accessed\":\"2026-01-01T00:00:00\",\"last_updated\":\"2026-01-01T00:00:00\","
                "\"last_checkpoint\":\"\",\"competency_index\":{}}"
            )
    return ""


def _next_step_hint(tool_name: str, args: Dict[str, Any], mode: str = "new_course",
                    context: Optional[Dict[str, Any]] = None) -> str:
    """
    Return a hint about what to do next after a successful tool call.

    These hints guide the agent toward the next logical action.
    They should be adaptive and use teacher judgment, not rigid rules.

    Args:
        tool_name: Name of the tool that was called
        args: Arguments passed to the tool
        mode: Session mode — "new_course" or "resume_course"
        context: Current course context with current_module, current_lesson, progress

    Returns:
        Hint string, or empty string if no hint needed
    """
    artifact = args.get("artifact_name", "")
    curr_module = context.get("current_module", 0) if context else 0
    curr_lesson = context.get("current_lesson", 0) if context else 0
    curr_progress = context.get("progress", 0.0) if context else 0.0

    if tool_name == "write_artifact":
        # After writing an artifact, continue with the workflow
        return f"Saved {artifact}. Continue with the next step of your plan."

    elif tool_name == "read_artifact":
        if artifact == "state.json":
            if mode == "resume_course":
                return (
                    f"Current progress: module {curr_module}, lesson {curr_lesson}, "
                    f"progress {curr_progress:.0%}. "
                    f"Resume teaching from where the learner left off."
                )
            return (
                f"Current progress: module {curr_module}, lesson {curr_lesson}, "
                f"progress {curr_progress:.0%}. Continue with your task."
            )
        else:
            return f"You have {artifact}. Continue with your task."

    elif tool_name == "update_state":
        # Parse the state_json to validate
        import json as _json
        try:
            new_state = _json.loads(args.get("state_json", "{}"))
        except Exception:
            new_state = {}

        new_module = new_state.get("current_module", -1)
        new_lesson = new_state.get("current_lesson", -1)
        new_status = new_state.get("status", "")
        new_progress = new_state.get("progress", -1)

        # Validate: lesson should increment, not reset to 0
        if new_lesson == 0 and curr_lesson > 0:
            return (
                f"ERROR: You set current_lesson to 0 but it was already {curr_lesson}. "
                f"Increment it to {curr_lesson + 1}. "
                f"NEVER reset current_lesson to 0 unless advancing to a new module. "
                f"Required: current_module={curr_module}, current_lesson={curr_lesson + 1}, "
                f"progress={min(1.0, curr_progress + 0.1):.2f}, status='active', "
                f"last_accessed=<ISO timestamp>, last_updated=<ISO timestamp>"
            )

        # Validate: lesson should match expected next lesson
        if new_lesson != -1 and new_lesson != curr_lesson + 1 and curr_lesson > 0:
            return (
                f"WARNING: You set current_lesson to {new_lesson} but expected {curr_lesson + 1}. "
                f"Current state: module {curr_module}, lesson {curr_lesson}. "
                f"Set current_lesson to {curr_lesson + 1} to advance correctly. "
                f"Include last_accessed and last_updated as ISO timestamps."
            )

        if new_status == "active" and curr_lesson == 0:
            return (
                "Status is now ACTIVE. Begin teaching Module 1, Lesson 1. "
                "Read the course plan to know what to teach, then deliver the lesson content. "
                "After teaching, when the learner is ready to continue, "
                "call update_state to advance to the next lesson."
            )
        elif new_status == "completed":
            return "Course is complete! Congratulate the learner."
        elif new_status == "active":
            return (
                f"State updated: module {new_module}, lesson {new_lesson}, progress {new_progress:.0%}. "
                f"Continue teaching. After the learner demonstrates understanding, "
                f"call update_state to advance to lesson {new_lesson + 1}."
            )

        return (
            "State updated. Required fields: current_module (int), current_lesson (int), "
            "progress (float 0-1), status (string), last_accessed (ISO), last_updated (ISO). "
            "IMPORTANT: current_lesson must be incremented by 1, never reset to 0. "
            "ALWAYS include last_accessed and last_updated as current ISO timestamps."
        )

    elif tool_name == "create_workspace":
        return "Workspace created. Continue with your task."

    elif tool_name == "list_courses":
        return "Here are the available courses."

    elif tool_name == "list_artifacts":
        return "Here are the artifacts in this course."

    elif tool_name == "list_uploads":
        return "Here are the uploaded files."

    return ""


def _get_mode_block(mode: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Return the mode-specific instruction block for the system prompt.

    Args:
        mode: Session mode — "new_course" or "resume_course"
        context: Optional context data for the agent

    Returns:
        Mode-specific instruction block
    """
    course_name = context.get("course_name", "the course") if context else "the course"
    status = context.get("status", "unknown") if context else "unknown"

    if mode == "new_course":
        return f"""
[MODE: new_course]
You are creating a new course called '{course_name}'.

WORKFLOW:

1. Interview the learner to understand their goals, knowledge, and context.
   - Ask adaptive questions based on the subject (see instructions §6)
   - Do NOT use a fixed questionnaire — let the subject guide your inquiry
   - Determine their knowledge through conversation and evidence, not self-assessment
   - Ask only questions whose answers will materially improve the curriculum

2. Once you have sufficient understanding, design the curriculum:
   - Analyze the subject and determine the mastery model
   - Build from foundations toward advanced concepts
   - Organize by logical dependencies, not arbitrary ordering
   - Write definition.json with the learner profile
   - Write planner.md with the full learning roadmap

3. Present the course plan to the learner for approval.
   - Show the roadmap and ask if it looks good
   - Be prepared to adjust based on feedback

4. Once approved, update state to active and begin teaching.

IMPORTANT:
- Use your judgment throughout — do not follow a rigid script
- The interview should feel like an intelligent conversation
- Adapt your questioning to the domain (programming, history, math, etc.)
- Write artifacts when you have enough information, not before
- Do not ask the learner to define their own level — determine it through evidence
"""
    elif mode == "resume_course":
        return f"""
[MODE: resume_course]
You are resuming an existing course called '{course_name}' (status: {status}).

WORKFLOW:
1. Read the course state to find current position (module, lesson, progress)
2. Read the course plan to see the full roadmap
3. Read the learner profile to understand their background
4. Read any session context from previous sessions
5. Resume teaching from where the learner left off

IMPORTANT:
- The workspace already exists — do not create it again
- The learner has already been interviewed — do not repeat the interview
- Do not restart from the beginning unless there is a clear reason
- Start teaching immediately after reading the necessary context
- Use your judgment about what to review vs. what to skip
"""
    return ""


def run(prompt: str, context: Optional[Dict[str, Any]] = None, verbose: bool = False,
        history: Optional[list] = None, mode: str = "new_course") -> str:
    """
    Run the Sensei agent with the given prompt and context.

    Uses the API's native function calling — no text-based tool call parsing.
    The API returns structured tool_calls or text; we dispatch accordingly.

    Args:
        prompt: The user prompt to process
        context: Optional context data for the agent
        verbose: If True, print tool call progress (default: False)
        history: Optional list of prior conversation messages [{"role": ..., "content": ...}]
        mode: Session mode — "new_course" or "resume_course"

    Returns:
        The final generated response from the agent
    """
    # Load agent instructions
    instructions = load_instructions()

    # Get tool schemas for the prompt (informational only — tools are called via API)
    tool_schemas = get_tool_schemas_for_prompt()

    # Build mode-specific instruction block
    mode_block = _get_mode_block(mode, context)

    # Build the system prompt with instructions, tools, and mode
    system_prompt = f"{instructions}\n\n{tool_schemas}\n\n{mode_block}"

    # Initialize conversation history
    conversation = [
        {"role": "system", "content": system_prompt}
    ]

    # Add prior history if provided
    if history:
        conversation.extend(history)

    # Add current user prompt
    conversation.append({"role": "user", "content": prompt})

    # Add context if provided
    if context:
        conversation.append({
            "role": "user",
            "content": f"Context: {context}"
        })

    # Tool calling loop
    tool_call_history = []  # Track recent tool calls for loop detection

    for iteration in range(MAX_TOOL_CALLS):
        # Build full prompt from conversation history
        full_prompt = "\n\n".join([
            msg["content"] for msg in conversation
        ])

        # Generate response — returns {"type": "text", ...} or {"type": "tool_calls", ...}
        result = generate(full_prompt)

        if result["type"] == "text":
            # Final text response — no tool calls
            content = result["content"]
            if content and content.strip():
                return content
            # Empty text after tool loop — nudge the model
            conversation.append({"role": "assistant", "content": content})
            conversation.append({
                "role": "user",
                "content": (
                    "Your response was empty. You must produce teaching content for the learner. "
                    "Continue with the lesson now."
                )
            })
            continue

        elif result["type"] == "tool_calls":
            calls = result["calls"]
            if not calls:
                return "I'm not sure how to respond to that. Could you rephrase?"

            # Execute each tool call
            for call in calls:
                tool_name = call["name"]
                tool_args = call["args"]

                # Loop detection: if same tool+artifact called 3+ times in last 5 calls, break out
                # Use tool:artifact key so read_artifact(file_a) and read_artifact(file_b) don't collide
                artifact_key = tool_args.get("artifact_name", "")
                call_key = f"{tool_name}:{artifact_key}" if artifact_key else tool_name
                tool_call_history.append(call_key)
                recent = tool_call_history[-5:]
                if recent.count(call_key) >= 3:
                    conversation.append({
                        "role": "user",
                        "content": (
                            f"STOP. You have called {tool_name}({artifact_key}) {recent.count(call_key)} times in the last "
                            f"{len(recent)} tool calls. This is a loop. You must STOP calling tools and "
                            "produce a text response for the learner RIGHT NOW. "
                            "If you need to teach, just teach — do not read or write any more files. "
                            "If you need to present something, just present it — do not call tools. "
                            "Respond with text only."
                        )
                    })
                    tool_call_history.clear()
                    break

                if verbose:
                    print(f"  Calling {tool_name}...")

                tool_result = execute_tool(tool_name, tool_args)

                if verbose:
                    print(f"  Result: {'success' if tool_result['success'] else tool_result['error']}")

                log_tool(
                    tool_name,
                    tool_args,
                    "success" if tool_result["success"] else tool_result["error"],
                )

                # Add tool result to conversation for the model to see
                conversation.append({
                    "role": "assistant",
                    "content": f"Called tool: {tool_name}"
                })
                conversation.append({
                    "role": "user",
                    "content": format_tool_result(tool_name, tool_args, tool_result, mode=mode, context=context)
                })

            # Continue loop — model should now produce text or more tool calls
            continue

    # Hit max iterations
    if "response" in dir() and isinstance(result, dict) and result.get("content"):
        return result["content"]
    return "I apologize — I got stuck trying to process that. Could you tell me what you'd like to continue with?"


def run_stream(prompt: str, context: Optional[Dict[str, Any]] = None, verbose: bool = False,
               history: Optional[list] = None, mode: str = "new_course") -> Generator[str, None, None]:
    """
    Run the Sensei agent with streaming responses.

    Same logic as run(), but yields text chunks for streaming display.
    Tool calls are executed synchronously; only the final text is streamed.

    Args:
        prompt: The user prompt to process
        context: Optional context data for the agent
        verbose: If True, print tool call progress
        history: Optional list of prior conversation messages
        mode: Session mode — "new_course" or "resume_course"

    Yields:
        Text chunks from the agent's response
    """
    instructions = load_instructions()
    tool_schemas = get_tool_schemas_for_prompt()
    mode_block = _get_mode_block(mode, context)
    system_prompt = f"{instructions}\n\n{tool_schemas}\n\n{mode_block}"

    conversation = [{"role": "system", "content": system_prompt}]

    if history:
        conversation.extend(history)

    conversation.append({"role": "user", "content": prompt})

    if context:
        conversation.append({"role": "user", "content": f"Context: {context}"})

    tool_call_history = []

    for iteration in range(MAX_TOOL_CALLS):
        full_prompt = "\n\n".join([msg["content"] for msg in conversation])

        # Stream the response
        text_buffer = ""
        tool_calls = None

        for chunk in generate_stream(full_prompt):
            if chunk["type"] == "text":
                text_buffer += chunk["content"]
                yield chunk["content"]
            elif chunk["type"] == "tool_calls":
                tool_calls = chunk["calls"]

        # If we got tool calls, execute them (text was already yielded above for any partial text)
        if tool_calls:
            # Add the accumulated text to conversation if any
            if text_buffer:
                conversation.append({"role": "assistant", "content": text_buffer})

            for call in tool_calls:
                tool_name = call["name"]
                tool_args = call["args"]

                # Loop detection — track tool:artifact, not just tool
                artifact_key = tool_args.get("artifact_name", "")
                call_key = f"{tool_name}:{artifact_key}" if artifact_key else tool_name
                tool_call_history.append(call_key)
                recent = tool_call_history[-5:]
                if recent.count(call_key) >= 3:
                    loop_msg = (
                        f"STOP. You have called {tool_name}({artifact_key}) {recent.count(call_key)} times. "
                        "Produce a text response for the learner RIGHT NOW."
                    )
                    conversation.append({"role": "user", "content": loop_msg})
                    tool_call_history.clear()
                    break

                if verbose:
                    print(f"  Calling {tool_name}...")

                tool_result = execute_tool(tool_name, tool_args)

                if verbose:
                    print(f"  Result: {'success' if tool_result['success'] else tool_result['error']}")

                log_tool(tool_name, tool_args, "success" if tool_result["success"] else tool_result["error"])

                conversation.append({"role": "assistant", "content": f"Called tool: {tool_name}"})
                conversation.append({
                    "role": "user",
                    "content": format_tool_result(tool_name, tool_args, tool_result, mode=mode, context=context)
                })

            continue

        # No tool calls — text was already yielded. Check if we need to continue.
        if text_buffer and text_buffer.strip():
            # Got a complete text response, done
            # State auto-advance is handled by Session._auto_advance_lesson()
            return

        # Empty text — nudge the model
        conversation.append({"role": "assistant", "content": text_buffer})
        conversation.append({
            "role": "user",
            "content": "Your response was empty. Produce teaching content for the learner."
        })
        continue

    yield "\n\nI apologize — I got stuck. Could you tell me what you'd like to continue with?"


def run_simple(prompt: str) -> str:
    """
    Simple run without tool calling loop.

    For cases where you just want a single LLM response
    without tool execution.

    Args:
        prompt: The user prompt to process

    Returns:
        The generated response from the agent
    """
    instructions = load_instructions()
    tool_schemas = get_tool_schemas_for_prompt()
    full_prompt = f"{instructions}\n\n{tool_schemas}\n\n---\n\nUser prompt: {prompt}"
    result = generate(full_prompt)
    if result["type"] == "text":
        return result["content"]
    return ""
