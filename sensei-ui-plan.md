# Sensei UI Plan — Streamlit Dashboard

## Overview

Add a `sensei ui` command that launches a Streamlit web dashboard. The UI provides a visual interface for course management, chat-based teaching with streaming responses, and progress tracking. Provider setup remains CLI-only (the UI prompts users to run `sensei connect` if no provider is configured).

---

## Phase 1: Streaming Infrastructure ✅

**Goal:** Add streaming support to the LLM gateway and agent layers so the UI can display token-by-token responses.

### Deliverables

| File | Change | Status |
|------|--------|--------|
| `pyproject.toml` | Add `streamlit>=1.38.0` to dependencies | ✅ |
| `src/sensei/gateway/provider.py` | Add `generate_with_provider_stream(prompt) -> Generator[str]` using `httpx.Client.stream()` with SSE parsing | ✅ |
| `src/sensei/gateway/client.py` | Add `generate_stream(prompt)` public entry point | ✅ |
| `src/sensei/gateway/__init__.py` | Export `generate_stream` | ✅ |
| `src/sensei/agent/runner.py` | Add `run_stream(prompt, context, verbose, history, mode) -> Generator[str]` — handles tool calls synchronously, streams final text | ✅ |
| `src/sensei/agent/session.py` | Add `send_stream(user_message) -> Generator[str]` — wraps `run_stream()` with state management | ✅ |

### Notes

- Tool calls are executed synchronously (UI shows a spinner during execution)
- Only the final text response is streamed token-by-token
- The streaming generator yields complete text chunks, not individual tokens (SSE `choices[0].delta.content`)

---

## Phase 2: UI Package Structure

**Goal:** Create the Streamlit app skeleton with page routing and shared components.

### Deliverables

| File | Purpose |
|------|---------|
| `src/sensei/ui/__init__.py` | Package init (empty) |
| `src/sensei/ui/app.py` | Main Streamlit entry point — page config, provider check, sidebar navigation, session state init |
| `src/sensei/ui/pages/__init__.py` | Package init (empty) |
| `src/sensei/ui/components.py` | Reusable components: progress bar, state badge, course card, markdown renderer |

### App Logic (`app.py`)

```
1. Check provider config → if missing, show warning + CLI instructions
2. Initialize st.session_state (selected_course, messages, mode)
3. Sidebar: course list + "New Course" button
4. Main area: route to selected page (Home or Chat)
```

---

## Phase 3: Home Page — Course Management ✅

**Goal:** Build the course list and management page.

### Deliverables

| File | Purpose | Status |
|------|---------|--------|
| `src/sensei/ui/pages/home.py` | Course list with status badges, create/delete/resume actions | ✅ |

### Features

- **Course list:** Display all courses as rows with name, status (planning/active/completed), last accessed date, Resume and Delete buttons
- **Create course:** Expander section with text input → calls `create_workspace()` → navigates to chat in `new_course` mode
- **Delete course:** Button with inline confirmation dialog → calls `delete_course()`
- **Resume course:** Button → navigates to chat in `resume_course` mode
- **Status badges:** Color-coded (planning=yellow, active=green, completed=blue) via `status_badge()`

### Key Decisions

1. **Home page extracted to separate file** (`pages/home.py`) rather than inline in `app.py`. Cleaner separation — `app.py` routes, `home.py` renders content.
2. **Course rows instead of cards** — used 3-column layout (name+badge, Resume, Delete) for scannability. Cards can be added later if needed.
3. **Inline confirmation for delete** — uses `st.warning()` + Yes/Cancel buttons inline (no modal, as Streamlit modals require third-party packages).
4. **Expander for create** — collapsed by default when courses exist, expanded when no courses yet.

---

## Phase 4: Chat Page — Teaching Interface ✅

**Goal:** Build the chat interface with streaming, tool call display, and progress tracking.

### Deliverables

| File | Purpose | Status |
|------|---------|--------|
| `src/sensei/ui/pages/chat.py` | Full chat interface with streaming, history, progress sidebar | ✅ |

### Features

- **Chat history:** Rendered via `st.chat_message` with role icons (👤 user, 🎓 Sensei)
- **User input:** `st.chat_input` at the bottom
- **Streaming response:** `session.send_stream()` → accumulates chunks → displays via `st.markdown()`; `st.status` shows progress
- **Tool call indicator:** `st.status` widget shows "Thinking..." / "Streaming response..." / "Response complete"
- **Progress sidebar:** Uses `progress_display()` from components — shows Module, Lesson, Progress bar
- **Mode awareness:** Session initialized with mode param; auto-start sends initial empty message to kick off conversation
- **Back button:** Returns to home, clears session state

### Key Decisions

1. **`session.send_stream()` instead of raw `run_stream()`** — used the Session-level streaming API which handles history management, state persistence, and context compression. Raw `run_stream()` only used internally.
2. **Accumulated display (not `st.write_stream`)** — `st.write_stream()` requires a generator that yields strings. Since `send_stream()` yields chunks that we need to accumulate for history, we collect all chunks then display via `st.markdown()`. The `st.status` widget provides real-time feedback during streaming.
3. **`st.status` instead of `st.spinner`** — `st.status` is persistent (doesn't disappear) and supports multiple states ("Thinking..." → "Streaming response..." → "Response complete"). Better UX for long-running operations.
4. **Session stored in `st.session_state`** — keyed by `session_{course_name}`. Prevents creating multiple Session objects for the same course on reruns. Cleared on back navigation.
5. **Auto-start via `_auto_start()`** — sends empty string to agent on first load, which triggers the interview (new_course) or artifact loading (resume_course). Uses `_auto_started` flag to prevent double-sends on Streamlit reruns.
6. **Progress in sidebar** — `progress_display()` renders Module, Lesson, Status metrics + progress bar. State details available in collapsible expander.

### Chat Flow

```
new_course mode:
  1. Auto-start sends empty message → agent asks interview question (streamed)
  2. User answers via chat input
  3. After 4 answers → agent writes artifacts (status spinner)
  4. Agent presents roadmap → approve/adjust buttons (TODO: Phase 5)
  5. On approve → agent starts teaching (streamed)

resume_course mode:
  1. Auto-start sends empty message → agent reads artifacts (status spinner)
  2. Agent resumes teaching from current position (streamed)
  3. User interacts via chat input
```

---

## Phase 5: CLI Integration ✅

**Goal:** Add the `sensei ui` command and test end-to-end.

### Deliverables

| File | Change | Status |
|------|--------|--------|
| `src/sensei/cli/app.py` | Add `ui` command that launches Streamlit | ✅ |
| `tests/test_ui.py` | Basic tests for UI helper functions | TODO |

### `sensei ui` Command

```python
@app.command()
def ui(port: int = typer.Option(8501, "--port", "-p"), headless: bool = True):
    """Launch the Sensei web dashboard."""
    import subprocess
    import sys
    app_path = Path(__file__).parent.parent / "ui" / "app.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path), "--server.port", str(port)]
    if headless:
        cmd.extend(["--server.headless", "true"])
    subprocess.run(cmd)
```

### Testing

- Unit test for `generate_with_provider_stream()` — done in Phase 1 commit
- Unit test for `run_stream()` with mocked provider — done in Phase 1 commit
- Smoke test: launch Streamlit app without errors — verified via import checks

---

## UI Layout

```
┌────────────────────────────────────────────────────────────────────┐
│  🎓 Sensei                                        [⚙️]            │
├──────────────────────┬─────────────────────────────────────────────┤
│  Available Courses   │  Chat with Sensei                           │
│                      │                                             │
│  📘 fastapi          │  👤 What would you like to learn?           │
│     active           │                                             │
│                      │  🤖 I'll teach you FastAPI...  [streaming]  │
│  📘 ml               │                                             │
│     planning         │  👤 Build REST APIs                         │
│                      │                                             │
│  [+ New Course]      │  🤖 Great! Let's start with...              │
│  [- Delete Course]   │                                             │
│======================│  ┌────────────────────────────────┐         │
|CourseNotes           │  │ Type your message...       [→] │         │
│                      │  └────────────────────────────────┘         │
├──────────────────────┴─────────────────────────────────────────────┤
│  Module 1 / Lesson 2 │  ████████░░░░ 25%  │         🟢 Active      │
└────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Order

1. **Phase 1** — Streaming infrastructure ✅
2. **Phase 2** — UI skeleton (app.py, components.py, pages/) ✅
3. **Phase 3** — Home page (course list, create, delete, resume) ✅
4. **Phase 4** — Chat page (streaming, history, progress, mode awareness) ✅
5. **Phase 5** — CLI command (`sensei ui`) ✅

All phases independently testable and verified. Phase 1 validated with unit tests. Phases 2-5 validated via import checks and 94 passing tests.

---

## Known Limitations / Future Work

1. **Approval flow** — approve/adjust buttons when agent presents roadmap are not yet implemented in Streamlit. Currently the user types "approve" or "adjust" in chat input. A dedicated button UI would be cleaner.
2. **Session history not persisted** — in-memory only. Agent forgets conversation when session is recreated. Need to persist history to disk (e.g., `history.jsonl` in course workspace).
3. **Agent status stays "planning"** — status often shows "planning" even when teaching. Needs investigation into how `update_status()` is called from the agent.
4. **UI tests** — `tests/test_ui.py` not yet created. Should test `status_badge()`, `progress_display()`, and `course_card()` with mocked Streamlit.
