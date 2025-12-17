# Gemini Project: TMSmini_.vGemini

This document provides an overview of the TMSmini_.vGemini project and instructions for development.

## Project Overview

This project appears to be a transportation management system (TMS) with a frontend and a backend. The project is structured as a monorepo with separate directories for the frontend and backend.

## spec-kit Integration

`github/spec-kit` has been integrated into this project to facilitate spec-driven development.

### Initialization

`spec-kit` was initialized with the following command:

```bash
.\.venv\Scripts\specify.exe init --here --ai gemini --force --script ps
```

This command created the `.specify` directory and configured the project to use the Gemini AI assistant.

### Usage

You can now use `spec-kit`'s slash commands to guide your development process:

*   `/speckit.constitution` - Establish project principles
*   `/speckit.specify` - Create baseline specification
*   `/speckit.plan` - Create implementation plan
*   `/speckit.tasks` - Generate actionable tasks
*   `/speckit.implement` - Execute implementation

## Development

The project is divided into a `frontend` and a `backend` directory.

### Backend

The backend is a Python project. To install dependencies, run:

```bash
pip install -r backend/requirements.txt
```

### Frontend

The frontend is a JavaScript project. To install dependencies, run:

```bash
npm install --prefix frontend
```
