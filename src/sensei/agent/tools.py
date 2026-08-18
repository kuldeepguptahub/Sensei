"""
Tool schemas for the Sensei agent.

Defines JSON schemas for skills that the LLM can invoke
and converts them to OpenAI function calling format.
"""

from typing import Dict, Any, List


# Max tool calls per run()
MAX_TOOL_CALLS = 10

# Max retries per tool call
MAX_RETRIES = 3


# Tool schemas - defines what parameters each tool accepts
TOOL_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "create_workspace": {
        "description": "Create a new course workspace with artifacts and uploads directories",
        "parameters": {
            "type": "object",
            "properties": {
                "course_name": {
                    "type": "string",
                    "description": "Name of the course to create"
                }
            },
            "required": ["course_name"]
        }
    },
    "list_courses": {
        "description": "List all available courses",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "delete_course": {
        "description": "Delete a course workspace and all its contents",
        "parameters": {
            "type": "object",
            "properties": {
                "course_name": {
                    "type": "string",
                    "description": "Name of the course to delete"
                }
            },
            "required": ["course_name"]
        }
    },
    "rename_course": {
        "description": "Rename an existing course",
        "parameters": {
            "type": "object",
            "properties": {
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
        }
    },
    "read_artifact": {
        "description": "Read an artifact file from a course workspace",
        "parameters": {
            "type": "object",
            "properties": {
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
        }
    },
    "write_artifact": {
        "description": "Write content to an artifact file in a course workspace",
        "parameters": {
            "type": "object",
            "properties": {
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
        }
    },
    "list_artifacts": {
        "description": "List all artifacts in a course workspace",
        "parameters": {
            "type": "object",
            "properties": {
                "course_name": {
                    "type": "string",
                    "description": "Name of the course"
                }
            },
            "required": ["course_name"]
        }
    },
    "workspace_exists": {
        "description": "Check if a course workspace exists",
        "parameters": {
            "type": "object",
            "properties": {
                "course_name": {
                    "type": "string",
                    "description": "Name of the course to check"
                }
            },
            "required": ["course_name"]
        }
    },
    "save_upload": {
        "description": "Save an uploaded file to a course workspace",
        "parameters": {
            "type": "object",
            "properties": {
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
        }
    },
    "read_upload": {
        "description": "Read an uploaded file from a course workspace",
        "parameters": {
            "type": "object",
            "properties": {
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
        }
    },
    "list_uploads": {
        "description": "List all uploaded files in a course workspace",
        "parameters": {
            "type": "object",
            "properties": {
                "course_name": {
                    "type": "string",
                    "description": "Name of the course"
                }
            },
            "required": ["course_name"]
        }
    },
    "update_state": {
        "description": "Update the state.json file for a course with new progress data",
        "parameters": {
            "type": "object",
            "properties": {
                "course_name": {
                    "type": "string",
                    "description": "Name of the course"
                },
                "state_json": {
                    "type": "string",
                    "description": "JSON string of the updated state object"
                }
            },
            "required": ["course_name", "state_json"]
        }
    }
}


def get_openai_tool_definitions() -> List[Dict[str, Any]]:
    """
    Convert TOOL_SCHEMAS to OpenAI function calling format.

    Returns:
        List of tool definitions for the API payload
    """
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": schema["description"],
                "parameters": schema["parameters"],
            }
        }
        for name, schema in TOOL_SCHEMAS.items()
    ]


def get_tool_schemas_for_prompt() -> str:
    """
    Generate a formatted tool schemas section for the LLM prompt.

    Returns:
        Formatted string describing all available tools
    """
    lines = ["Available tools:"]

    for name, schema in TOOL_SCHEMAS.items():
        params = schema.get("parameters", {}).get("properties", {})
        required = schema.get("parameters", {}).get("required", [])

        # Build parameter list
        param_parts = []
        for param_name, param_info in params.items():
            suffix = " (required)" if param_name in required else ""
            param_parts.append(f"{param_name}: {param_info['type']}{suffix}")

        params_str = ", ".join(param_parts) if param_parts else "none"
        lines.append(f"- {name}({params_str}) — {schema['description']}")

    return "\n".join(lines)
