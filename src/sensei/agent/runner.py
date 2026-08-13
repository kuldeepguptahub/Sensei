"""
Agent runner for Sensei.

This module is responsible for:
- Loading agent instructions
- Registering skills
- Invoking the gateway
- Parsing and executing tool calls
- Returning responses
"""

import time
from pathlib import Path
from typing import Dict, Any, Optional
from ..gateway.client import generate
from .tools import (
    TOOL_CALL_START,
    TOOL_CALL_END,
    MAX_TOOL_CALLS,
    MAX_RETRIES,
    parse_tool_call,
    get_tool_schemas_for_prompt,
)
from .registry import get_skill


def load_instructions() -> str:
    """
    Load the agent instructions from instructions.md.

    Returns:
        The content of the instructions file

    Raises:
        FileNotFoundError: If the instructions file doesn't exist
    """
    instructions_path = Path(__file__).parent / "instructions.md"
    return instructions_path.read_text(encoding='utf-8')


def execute_tool(tool_name: str, args: Dict[str, str]) -> Dict[str, Any]:
    """
    Execute a tool call with retry logic.

    Args:
        tool_name: Name of the tool to execute
        args: Arguments to pass to the tool

    Returns:
        Dict with 'success' key and either 'data' or 'error'
    """
    for attempt in range(MAX_RETRIES):
        try:
            skill = get_skill(tool_name)
            result = skill(**args)
            return {"success": True, "data": result}
        except KeyError:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        except TypeError as e:
            return {"success": False, "error": f"Invalid arguments: {e}"}
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            return {"success": False, "error": str(e)}

    return {"success": False, "error": f"Failed after {MAX_RETRIES} attempts"}


def format_tool_result(result: Dict[str, Any]) -> str:
    """
    Format a tool result for inclusion in the conversation.

    Args:
        result: Tool execution result dict

    Returns:
        Formatted string for the LLM
    """
    if result["success"]:
        data = result.get("data")
        if data is None:
            return "<tool_result>\nsuccess: true\n</tool_result>"
        elif isinstance(data, str):
            return f"<tool_result>\nsuccess: true\ndata: {data}\n</tool_result>"
        else:
            return f"<tool_result>\nsuccess: true\ndata: {data}\n</tool_result>"
    else:
        return f"<tool_result>\nsuccess: false\nerror: {result['error']}\n</tool_result>"


def has_tool_call(text: str) -> bool:
    """
    Check if the response contains a tool call.

    Args:
        text: LLM response text

    Returns:
        True if tool call found, False otherwise
    """
    return TOOL_CALL_START in text and TOOL_CALL_END in text


def extract_text_before_tool_call(text: str) -> str:
    """
    Extract text before a tool call (if any).

    Args:
        text: LLM response text

    Returns:
        Text before the tool call, or full text if no tool call
    """
    if TOOL_CALL_START in text:
        idx = text.index(TOOL_CALL_START)
        return text[:idx].strip()
    return text


def run(prompt: str, context: Optional[Dict[str, Any]] = None, verbose: bool = False) -> str:
    """
    Run the Sensei agent with the given prompt and context.

    Supports tool calling loop - will execute tools and feed results
    back to the LLM until a final text response is produced.

    Args:
        prompt: The user prompt to process
        context: Optional context data for the agent
        verbose: If True, print tool call progress (default: False)

    Returns:
        The final generated response from the agent
    """
    # Load agent instructions
    instructions = load_instructions()

    # Get tool schemas for the prompt
    tool_schemas = get_tool_schemas_for_prompt()

    # Build the system prompt with instructions and tools
    system_prompt = f"{instructions}\n\n{tool_schemas}"

    # Initialize conversation history
    conversation = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

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

        # Generate response
        response = generate(full_prompt)

        # Check for tool call
        if has_tool_call(response):
            # Extract any text before the tool call
            text_before = extract_text_before_tool_call(response)

            # Parse the tool call
            tool_call = parse_tool_call(response)

            if tool_call is None:
                # Malformed tool call, return what we have
                return response

            # Execute the tool
            if verbose:
                print(f"  Calling {tool_call['name']}...")

            result = execute_tool(tool_call["name"], tool_call["args"])

            if verbose:
                print(f"  Result: {'success' if result['success'] else result['error']}")

            # Add the response and result to conversation
            conversation.append({
                "role": "assistant",
                "content": response
            })
            conversation.append({
                "role": "user",
                "content": format_tool_result(result)
            })

            # Continue to next iteration
            continue

        else:
            # No tool call - this is the final response
            return response

    # Hit max iterations, return last response
    return response


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
    return generate(full_prompt)
