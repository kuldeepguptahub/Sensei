# Changelog

All notable changes to Sensei will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.0] - 2026-08-03

### Added
- Agent runner with instructions loading and prompt assembly
- Skill registry with courses, artifacts, uploads, and workspace skills
- Course workspace creation with artifacts structure
- Artifact read/write/list operations
- Upload file management
- Workspace existence check

### Changed
- Migrated state management to skills-based architecture

## [0.0.4] - 2026-07-30

### Added
- State management module for course progress tracking
- Prompt template system for agent instructions
- Prompt assembly for combining instructions with user input
- Runtime module for agent execution

## [0.0.3] - 2026-07-28

### Added
- Gateway transport layer with retry logic
- Exponential backoff for transient failures
- Custom exception hierarchy for gateway errors
- Course management workflow (create, resume, complete)
- Course CRUD operations via persistence layer

## [0.0.2] - 2026-07-20

### Added
- SQLite persistence layer for course storage
- Database initialization and migration
- Course insert, get, update, delete operations
- Gateway configuration setup via CLI
- TOML config file support

## [0.0.1] - 2026-07-18

### Added
- CLI application bootstrap with Typer
- Setup command for provider configuration
- List courses command
- Start new course command
- Resume course command
- Complete course command

## [0.0.0] - 2026-07-14

### Added
- Initial project structure
- README with project vision
- Python package configuration
- Development environment setup
