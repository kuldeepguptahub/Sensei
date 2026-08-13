"""
Tool schemas for the Sensei agent.

Defines JSON schemas for skills that the LLM can invoke.
"""

from typing import Dict, Any, Optional


# Tool call marker
TOOL_CALL_START = "<tool_call>"
TOOL_CALL_END = "</tool_call>"

# Max tool calls per run()
MAX_TOOL_CALLS = 10

# Max retries per tool call
MAX_RETRIES = 3


# Tool schemas - defines what parameters each tool accepts
TOOL_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "create_workspace": {
        "description": "Create a new course workspace with artifacts and uploads directories",
        "parameters": {
            "course_name": {
                "type": "string",
                "description": "Name of the course to create"
            }
        },
        "required": ["course_name"]
    },
    "list_courses": {
        "description": "List all available courses",
        "parameters": {},
        "required": []
    },
    "delete_course": {
        "description": "Delete a course workspace and all its contents",
        "parameters": {
            "course_name": {
                "type": "string",
                "description": "Name of the course to delete"
            }
        },
        "required": ["course_name"]
    },
    "rename_course": {
        "description": "Rename an existing course",
        "parameters": {
            "old_name": {
                "type": "string",
                "description": "Current name of the course"
            },
            "new_name": {
                "type": "string",
                "description": "New name for the course"
            }
        },
        "required": ["old_name", "new_name"]
    },
    "read_artifact": {
        "description": "Read an artifact file from a course workspace",
        "parameters": {
            "course_name": {
                "type": "string",
                "description": "Name of the course"
            },
            "artifact_name": {
                "type": "string",
                "description": "Name of the artifact (e.g., 'definition.json', 'planner.md')"
            }
        },
        "required": ["course_name", "artifact_name"]
    },
    "write_artifact": {
        "description": "Write content to an artifact file in a course workspace",
        "parameters": {
            "course_name": {
                "type": "string",
                "description": "Name of the course"
            },
            "artifact_name": {
                "type": "string",
                "description": "Name of the artifact to write"
            },
            "content": {
                "type": "string",
                "description": "Content to write to the artifact"
            }
        },
        "required": ["course_name", "artifact_name", "content"]
    },
    "list_artifacts": {
        "description": "List all artifacts in a course workspace",
        "parameters": {
            "course_name": {
                "type": "string",
                "description": "Name of the course"
            }
        },
        "required": ["course_name"]
    },
    "workspace_exists": {
        "description": "Check if a course workspace exists",
        "parameters": {
            "course_name": {
                "type": "string",
                "description": "Name of the course to check"
            }
        },
        "required": ["course_name"]
    },
    "save_upload": {
        "description": "Save an uploaded file to a course workspace",
        "parameters": {
            "course_name": {
                "type": "string",
                "description": "Name of the course"
            },
            "file_name": {
                "type": "string",
                "description": "Name of the file to save"
            },
            "content": {
                "type": "string",
                "description": "Base64-encoded file content"
            }
        },
        "required": ["course_name", "file_name", "content"]
    },
    "read_upload": {
        "description": "Read an uploaded file from a course workspace",
        "parameters": {
            "course_name": {
                "type": "string",
                "description": "Name of the course"
            },
            "file_name": {
                "type": "string",
                "description": "Name of the file to read"
            }
        },
        "required": ["course_name", "file_name"]
    },
    "list_uploads": {
        "description": "List all uploaded files in a course workspace",
        "parameters": {
            "course_name": {
                "type": "string",
                "description": "Name of the course"
            }
        },
        "required": ["course_name"]
    }
}


def get_tool_schemas_for_prompt() -> str:
    """
    Generate a formatted tool schemas section for the LLM prompt.

    Returns:
        Formatted string describing all available tools
    """
    lines = ["Available tools:"]

    for name, schema in TOOL_SCHEMAS.items():
        params = schema.get("parameters", {})
        required = schema.get("required", [])

        # Build parameter list
        param_parts = []
        for param_name, param_info in params.items():
            suffix = " (required)" if param_name in required else ""
            param_parts.append(f"{param_name}: {param_info['type']}{suffix}")

        params_str = ", ".join(param_parts) if param_parts else "none"
        lines.append(f"- {name}({params_str}) — {schema['description']}")

    return "\n".join(lines)


def parse_tool_call(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse a tool call from LLM output.

    Expected format:
    <tool_call>
    name: function_name
    param1: value1
    param2: value2
    </tool_call>

    Args:
        text: LLM output text

    Returns:
        Dict with 'name' and 'args' keys, or None if no tool call found
    """
    if TOOL_CALL_START not in text or TOOL_CALL_END not in text:
        return None

    # Extract the tool call block
    start_idx = text.index(TOOL_CALL_START) + len(TOOL_CALL_START)
    end_idx = text.index(TOOL_CALL_END)
    tool_call_text = text[start_idx:end_idx].strip()

    # Parse the tool call
    lines = tool_call_text.split("\n")
    if not lines:
        return None

    # First line should be the tool name
    first_line = lines[0].strip()
    if not first_line.startswith("name:"):
        return None

    tool_name = first_line.replace("name:", "").strip()

    # Parse remaining lines as parameters
    args = {}
    for line in lines[1:]:
        line = line.strip()
        if ":" in line:
            key, value = line.split(":", 1)
            args[key.strip()] = value.strip()

    return {
        "name": tool_name,
        "args": args
    }
