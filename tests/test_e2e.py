"""
End-to-end tests for Sensei.

Tests the full flow: setup → start → teach → resume
with a mocked LLM provider.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import List


# ─── Fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def mock_courses_dir(tmp_path):
    """Mock COURSES_DIR to use a temp directory."""
    courses_dir = tmp_path / "courses"
    courses_dir.mkdir()
    with patch("sensei.path_utils.COURSES_DIR", courses_dir), \
         patch("sensei.skills.courses.COURSES_DIR", courses_dir), \
         patch("sensei.state.manager.COURSES_DIR", courses_dir):
        yield courses_dir


@pytest.fixture
def mock_config():
    """Mock config to return a valid provider config."""
    mock_cfg = MagicMock()
    mock_cfg.provider_name = "test-provider"
    mock_cfg.api_key = "test-key"
    mock_cfg.model_id = "test-model"
    mock_cfg.base_url = "https://test.example.com"
    mock_cfg.auth_header = "Authorization"
    mock_cfg.auth_prefix = "Bearer"
    mock_cfg.api_type = "openai"
    with patch("sensei.gateway.config.config_exists", return_value=True), \
         patch("sensei.gateway.config.load_config", return_value=mock_cfg):
        yield mock_cfg


# ─── Helper: Build Tool Call Responses ─────────────────────────────────


def tool_call_response(tool_name: str, args: dict) -> dict:
    """Build a structured tool call response."""
    return {
        "type": "tool_calls",
        "calls": [{"name": tool_name, "args": args}]
    }


def text_response(text: str) -> dict:
    """Build a structured text response."""
    return {"type": "text", "content": text}


# ─── E2E Test: Full Course Lifecycle ────────────────────────────────────


class TestE2ECourseLifecycle:
    """
    Tests the full course lifecycle:
    1. Create workspace
    2. Plan course (write definition.json + planner.md)
    3. Start teaching
    4. Resume course
    """

    def test_create_workspace_and_plan(self, mock_courses_dir, mock_config):
        """Test workspace creation and course planning via tool calls."""
        from sensei.skills.courses import create_workspace, list_courses
        from sensei.skills.artifacts import read_artifact, write_artifact
        from sensei.agent.session import Session

        # ── Step 1: Create workspace ──
        create_workspace("test-course")

        # Verify workspace structure
        course_dir = mock_courses_dir / "test-course"
        assert course_dir.exists()
        assert (course_dir / "artifacts").exists()
        assert (course_dir / "uploads").exists()
        assert (course_dir / "artifacts" / "definition.json").exists()
        assert (course_dir / "artifacts" / "state.json").exists()
        assert (course_dir / "artifacts" / "planner.md").exists()
        assert (course_dir / "artifacts" / "context.md").exists()

        # Verify initial state
        state = json.loads(read_artifact("test-course", "state.json"))
        assert state["status"] == "planning"
        assert state["progress"] == 0.0
        assert state["current_module"] == 0
        assert state["current_lesson"] == 0

        # ── Step 2: Simulate LLM writing definition.json ──
        definition = {
            "course_name": "test-course",
            "topic": "FastAPI",
            "goals": ["Build a REST API", "Learn async patterns"],
            "desired_outcome": "Production-ready API",
            "portfolio_project": "Task manager API",
            "current_knowledge": "Basic Python",
            "learning_style": "hands-on",
            "constraints": [],
            "completion_criteria": "Deploy working API"
        }
        write_artifact("test-course", "definition.json", json.dumps(definition, indent=2))

        # Verify definition was written
        loaded_def = json.loads(read_artifact("test-course", "definition.json"))
        assert loaded_def["topic"] == "FastAPI"
        assert len(loaded_def["goals"]) == 2

        # ── Step 3: Simulate LLM writing planner.md ──
        planner_content = """# Learning Roadmap

## Module 1: FastAPI Fundamentals
- Lesson 1.1: Setting up FastAPI
- Lesson 1.2: Request/Response models
- Lesson 1.3: Dependency injection

## Module 2: Advanced Patterns
- Lesson 2.1: Async/Await
- Lesson 2.2: Middleware
- Lesson 2.3: Database integration

## Module 3: Production Ready
- Lesson 3.1: Testing
- Lesson 3.2: Docker deployment
- Lesson 3.3: Monitoring
"""
        write_artifact("test-course", "planner.md", planner_content)

        # Verify planner was written
        loaded_planner = read_artifact("test-course", "planner.md")
        assert "Module 1: FastAPI Fundamentals" in loaded_planner
        assert "Module 2: Advanced Patterns" in loaded_planner

        # ── Step 4: Update state to active ──
        state["status"] = "active"
        state["current_module"] = 0
        state["current_lesson"] = 0
        write_artifact("test-course", "state.json", json.dumps(state, indent=2))

        # Verify state update
        final_state = json.loads(read_artifact("test-course", "state.json"))
        assert final_state["status"] == "active"

    def test_session_send_with_mocked_llm(self, mock_courses_dir, mock_config):
        """Test Session.send() with mocked LLM responses."""
        from sensei.skills.courses import create_workspace
        from sensei.agent.session import Session

        # Create workspace
        create_workspace("test-session")

        # Mock LLM responses for planning flow
        responses = [
            text_response(
                "I'll help you create a course on FastAPI. "
                "What's your current experience with Python web frameworks?"
            ),
            tool_call_response("write_artifact", {
                "course_name": "test-session",
                "artifact_name": "definition.json",
                "content": json.dumps({
                    "course_name": "test-session",
                    "topic": "FastAPI",
                    "goals": ["Build REST APIs"],
                    "desired_outcome": "Production API",
                    "portfolio_project": "Task manager",
                    "current_knowledge": "Basic Python",
                    "learning_style": "hands-on",
                    "constraints": [],
                    "completion_criteria": "Working API"
                })
            }),
            tool_call_response("write_artifact", {
                "course_name": "test-session",
                "artifact_name": "planner.md",
                "content": "# Learning Roadmap\n\n## Module 1: Basics\n- Lesson 1.1: Setup\n"
            }),
            text_response(
                "Here's your learning roadmap:\n\n"
                "## Module 1: Basics\n"
                "- Lesson 1.1: Setup\n\n"
                "Type 'approve' to start learning."
            ),
        ]

        response_idx = 0

        def mock_generate(prompt: str) -> str:
            nonlocal response_idx
            resp = responses[response_idx]
            response_idx += 1
            return resp

        # Create session and send planning prompt
        session = Session("test-session", verbose=False)

        # Mock at the runner level where generate is actually called
        with patch("sensei.agent.runner.generate", side_effect=mock_generate):
            response = session.send(
                "Create a new course called 'test-session'. "
                "Follow the planning workflow."
            )

        # Verify the agent responded
        assert response is not None
        assert len(response) > 0

        # Verify history was maintained
        assert len(session.history) >= 2  # At least user + assistant

    def test_session_resume(self, mock_courses_dir, mock_config):
        """Test session resumption loads context and continues."""
        from sensei.skills.courses import create_workspace
        from sensei.skills.artifacts import write_artifact
        from sensei.agent.session import Session

        # Create workspace with existing state
        create_workspace("test-resume")

        # Simulate a previous session's state
        state = {
            "current_module": 0,
            "current_lesson": 1,
            "competency_index": {"module_0": {"score": 8, "passed": True}},
            "last_accessed": "2026-08-17T10:00:00",
            "last_updated": "2026-08-17T10:00:00",
            "progress": 0.2,
            "status": "active",
            "last_checkpoint": ""
        }
        write_artifact("test-resume", "state.json", json.dumps(state, indent=2))

        # Write a context summary from previous session
        context = """# Course Context

## Previous Session Summary
- Covered: FastAPI setup, basic routing, request models
- Learner is comfortable with Python basics
- Next: Dependency injection and middleware
"""
        write_artifact("test-resume", "context.md", context)

        # Create session (should detect resumption context)
        session = Session("test-resume", verbose=False)
        assert session.has_context is True

        # Mock LLM response for resume
        resume_response = text_response(
            "Welcome back! Last time we covered FastAPI setup and basic routing. "
            "Let's continue with dependency injection."
        )

        def mock_generate(prompt: str) -> str:
            # Verify context was injected
            assert "Previous Session Summary" in prompt
            return resume_response

        with patch("sensei.agent.runner.generate", side_effect=mock_generate):
            response = session.send("Resume learning FastAPI")

        # Verify context was injected (has_context should be False after first send)
        assert session.has_context is False
        assert "Welcome back" in response

    def test_state_persistence_across_sessions(self, mock_courses_dir, mock_config):
        """Test that state persists and can be loaded in new sessions."""
        from sensei.skills.courses import create_workspace
        from sensei.skills.artifacts import write_artifact, read_artifact
        from sensei.agent.session import Session

        # Create workspace
        create_workspace("test-persist")

        # Simulate some progress
        state = {
            "current_module": 1,
            "current_lesson": 2,
            "competency_index": {"module_0": {"score": 9, "passed": True}, "module_1": {"score": 7, "passed": True}},
            "last_accessed": "2026-08-17T10:00:00",
            "last_updated": "2026-08-17T10:00:00",
            "progress": 0.45,
            "status": "active",
            "last_checkpoint": "2026-08-17T09:30:00"
        }
        write_artifact("test-persist", "state.json", json.dumps(state, indent=2))

        # Create first session
        session1 = Session("test-persist", verbose=False)
        assert session1.state["progress"] == 0.45
        assert session1.state["current_module"] == 1

        # Update progress
        session1.update_state(progress=0.55, current_lesson=3)

        # Verify state was saved
        saved_state = json.loads(read_artifact("test-persist", "state.json"))
        assert saved_state["progress"] == 0.55
        assert saved_state["current_lesson"] == 3

        # Create a new session (simulates app restart)
        session2 = Session("test-persist", verbose=False)
        assert session2.state["progress"] == 0.55
        assert session2.state["current_module"] == 1
        assert session2.state["current_lesson"] == 3


# ─── E2E Test: Tool Calling Flow ────────────────────────────────────────


class TestE2EToolCalling:
    """Tests tool calling execution in the agent runner."""

    def test_tool_execution_via_runner(self, mock_courses_dir, mock_config):
        """Test that tool calls are executed correctly by the runner."""
        from sensei.skills.courses import create_workspace
        from sensei.agent.runner import run

        # Create workspace
        create_workspace("test-tools")

        # Mock LLM to return a tool call then plain text
        call_count = 0

        def mock_generate(prompt: str) -> str:
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # First call: write definition.json
                return tool_call_response("write_artifact", {
                    "course_name": "test-tools",
                    "artifact_name": "definition.json",
                    "content": json.dumps({
                        "course_name": "test-tools",
                        "topic": "Testing",
                        "goals": ["Learn testing"],
                        "desired_outcome": "Test suite",
                        "portfolio_project": "Test project",
                        "current_knowledge": "None",
                        "learning_style": "hands-on",
                        "constraints": [],
                        "completion_criteria": "Tests pass"
                    })
                })
            else:
                # Subsequent calls: plain text
                return text_response("Definition written successfully!")

        with patch("sensei.agent.runner.generate", side_effect=mock_generate):
            response = run(
                prompt="Write the course definition",
                context={"course_name": "test-tools"},
                verbose=False
            )

        # Verify the tool was executed
        assert "Definition written" in response

        # Verify the file was actually written
        from sensei.skills.artifacts import read_artifact
        content = read_artifact("test-tools", "definition.json")
        data = json.loads(content)
        assert data["topic"] == "Testing"

    def test_multiple_tool_calls(self, mock_courses_dir, mock_config):
        """Test handling of multiple sequential tool calls."""
        from sensei.skills.courses import create_workspace
        from sensei.agent.runner import run

        create_workspace("test-multi")

        call_count = 0

        def mock_generate(prompt: str) -> str:
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # Write definition
                return tool_call_response("write_artifact", {
                    "course_name": "test-multi",
                    "artifact_name": "definition.json",
                    "content": json.dumps({
                        "course_name": "test-multi",
                        "topic": "Multi-tool",
                        "goals": ["Test multiple tools"],
                        "desired_outcome": "All tools work",
                        "portfolio_project": "Multi-tool test",
                        "current_knowledge": "Some",
                        "learning_style": "visual",
                        "constraints": [],
                        "completion_criteria": "Done"
                    })
                })
            elif call_count == 2:
                # Write planner
                return tool_call_response("write_artifact", {
                    "course_name": "test-multi",
                    "artifact_name": "planner.md",
                    "content": "# Roadmap\n\n## Module 1\n- Lesson 1.1\n"
                })
            else:
                return text_response("Both artifacts written!")

        with patch("sensei.agent.runner.generate", side_effect=mock_generate):
            response = run(
                prompt="Write definition and planner",
                context={"course_name": "test-multi"},
                verbose=False
            )

        assert "Both artifacts" in response

        from sensei.skills.artifacts import read_artifact
        planner = read_artifact("test-multi", "planner.md")
        assert "Module 1" in planner

    def test_tool_error_handling(self, mock_courses_dir, mock_config):
        """Test that tool errors are reported back to the LLM."""
        from sensei.skills.courses import create_workspace
        from sensei.agent.runner import run

        create_workspace("test-error")

        call_count = 0

        def mock_generate(prompt: str) -> str:
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # Try to write to nonexistent course
                return tool_call_response("write_artifact", {
                    "course_name": "nonexistent-course",
                    "artifact_name": "file.md",
                    "content": "test"
                })
            else:
                # LLM sees the error and responds gracefully
                return text_response(
                    "The tool reported an error because the course doesn't exist. "
                    "Please create the course first."
                )

        with patch("sensei.agent.runner.generate", side_effect=mock_generate):
            response = run(
                prompt="Write to nonexistent course",
                context={},
                verbose=False
            )

        # Error should be handled gracefully
        assert response is not None
        assert len(response) > 0


# ─── E2E Test: History Management ───────────────────────────────────────


class TestE2EHistoryManagement:
    """Tests conversation history and context compression."""

    def test_history_grows_with_turns(self, mock_courses_dir, mock_config):
        """Test that conversation history grows with each turn."""
        from sensei.skills.courses import create_workspace
        from sensei.agent.session import Session

        create_workspace("test-history")

        def mock_generate(prompt: str) -> str:
            return text_response("Response to your message.")

        session = Session("test-history", verbose=False, max_history=20)

        with patch("sensei.agent.runner.generate", side_effect=mock_generate):
            session.send("Message 1")
            session.send("Message 2")
            session.send("Message 3")

        # Each turn adds user + assistant = 2 messages
        assert len(session.history) == 6

    def test_history_compression(self, mock_courses_dir, mock_config):
        """Test that history is compressed when it exceeds the window."""
        from sensei.skills.courses import create_workspace
        from sensei.agent.session import Session

        create_workspace("test-compress")

        call_count = 0

        def mock_generate(prompt: str) -> str:
            nonlocal call_count
            call_count += 1

            if call_count <= 2:
                # First 2 calls: normal responses
                return text_response("Normal response.")
            else:
                # Compression call: return summary
                return text_response(
                    "## Session Summary\n"
                    "- Learner covered FastAPI basics\n"
                    "- Comfortable with Python\n"
                    "- Next: dependency injection"
                )

        # Use small max_history to trigger compression
        session = Session("test-compress", verbose=False, max_history=4)

        with patch("sensei.agent.runner.generate", side_effect=mock_generate):
            # Send enough messages to exceed max_history
            for i in range(5):
                session.send(f"Message {i}")

        # History should be compressed (trimmed to max_history)
        assert len(session.history) <= session.max_history

    def test_resumption_context_injection(self, mock_courses_dir, mock_config):
        """Test that context is injected on first message when resuming."""
        from sensei.skills.courses import create_workspace
        from sensei.skills.artifacts import write_artifact
        from sensei.agent.session import Session

        create_workspace("test-inject")

        # Write existing context
        write_artifact("test-inject", "context.md",
            "# Course Context\n\nPrevious session covered FastAPI basics.")

        session = Session("test-inject", verbose=False)
        assert session.has_context is True

        captured_prompts = []

        def mock_generate(prompt: str) -> str:
            captured_prompts.append(prompt)
            return text_response("Continuing from where we left off.")

        with patch("sensei.agent.runner.generate", side_effect=mock_generate):
            session.send("Continue learning")

        # First prompt should contain injected context
        assert "Previous session covered" in captured_prompts[0]
        assert session.has_context is False


# ─── E2E Test: Validation Integration ──────────────────────────────────


class TestE2EValidationIntegration:
    """Tests that validation is enforced throughout the flow."""

    def test_invalid_course_name_rejected(self, mock_courses_dir, mock_config):
        """Test that invalid course names are rejected at every level."""
        from sensei.skills.courses import create_workspace
        from sensei.validation import validate_course_name

        # Spaces are now allowed (converted to hyphens)
        assert validate_course_name("my course") == "my-course"

        # Should reject path traversal
        with pytest.raises(ValueError, match="Invalid course name"):
            validate_course_name("../../etc")

        # Should reject dots
        with pytest.raises(ValueError, match="Invalid course name"):
            validate_course_name("course.name")

    def test_invalid_artifact_name_rejected(self, mock_courses_dir, mock_config):
        """Test that invalid artifact names are rejected."""
        from sensei.skills.artifacts import write_artifact
        from sensei.skills.courses import create_workspace

        create_workspace("test-validation")

        # Should reject artifact names with path separators
        with pytest.raises(ValueError):
            write_artifact("test-validation", "../evil.md", "malicious")

        with pytest.raises(ValueError):
            write_artifact("test-validation", "dir/file.md", "malicious")

    def test_state_validation(self, mock_courses_dir, mock_config):
        """Test that state updates are validated."""
        from sensei.skills.courses import create_workspace, update_state
        import json

        create_workspace("test-state-validation")

        # Invalid status should be rejected
        invalid_state = json.dumps({
            "current_module": 0,
            "current_lesson": 0,
            "progress": 0.0,
            "status": "invalid_status"
        })
        with pytest.raises(ValueError, match="Invalid status"):
            update_state("test-state-validation", invalid_state)

        # Progress out of range should be rejected
        invalid_progress = json.dumps({
            "current_module": 0,
            "current_lesson": 0,
            "progress": 1.5,
            "status": "active"
        })
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            update_state("test-state-validation", invalid_progress)
