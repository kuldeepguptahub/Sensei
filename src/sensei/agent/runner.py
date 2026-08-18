"""
Agent runner for Sensei.

This module is responsible for:
- Loading agent instructions
- Registering skills
- Invoking the gateway
- Executing tool calls from structured API responses
- Returning responses
"""

import time
from pathlib import Path
from typing import Dict, Any, Optional
from ..gateway.client import generate
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
    skill = get_skill(name)
    if skill is None:
        return {"success": False, "error": f"Unknown tool: {name}"}

    try:
        result = skill(**args)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def format_tool_result(result: Dict[str, Any]) -> str:
    """
    Format a tool execution result for the conversation.

    Args:
        result: The tool execution result dict

    Returns:
        Formatted string for the conversation
    """
    if result["success"]:
        data = result.get("data")
        if data is None:
            return "<tool_result>\nsuccess: true\n</tool_result>"
        return f"<tool_result>\nsuccess: true\ndata: {data}\n</tool_result>"
    else:
        return f"<tool_result>\nsuccess: false\nerror: {result['error']}\n</tool_result>"


def run(prompt: str, context: Optional[Dict[str, Any]] = None, verbose: bool = False,
        history: Optional[list] = None) -> str:
    """
    Run the Sensei agent with the given prompt and context.

    Uses the API's native function calling — no text-based tool call parsing.
    The API returns structured tool_calls or text; we dispatch accordingly.

    Args:
        prompt: The user prompt to process
        context: Optional context data for the agent
        verbose: If True, print tool call progress (default: False)
        history: Optional list of prior conversation messages [{"role": ..., "content": ...}]

    Returns:
        The final generated response from the agent
    """
    # Load agent instructions
    instructions = load_instructions()

    # Get tool schemas for the prompt (informational only — tools are called via API)
    tool_schemas = get_tool_schemas_for_prompt()

    # Build the system prompt with instructions and tools
    system_prompt = f"{instructions}\n\n{tool_schemas}"

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
                # API said tool_calls but gave none — treat as text
                return "I'm not sure how to respond to that. Could you rephrase?"

            # Execute each tool call
            for call in calls:
                tool_name = call["name"]
                tool_args = call["args"]

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
                    "content": format_tool_result(tool_result)
                })

            # Continue loop — model should now produce text or more tool calls
            continue

    # Hit max iterations
    if "response" in dir() and isinstance(result, dict) and result.get("content"):
        return result["content"]
    return "I apologize — I got stuck trying to process that. Could you tell me what you'd like to continue with?"


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
