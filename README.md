# TMSmini Gemini Edition

This project is a mini Transport Management System (TMS) designed to automate and display freight offers. It features a modern web interface built with React and a powerful backend powered by FastAPI.

## Project Structure

- **/backend**: The FastAPI application that handles data, scraping, and API logic.
- **/frontend**: The React single-page application that provides the user interface.

## Prerequisites

- Python 3.9+
- Node.js 18+ and npm
- A running PostgreSQL database

## Setup and Installation

### 1. Backend Setup

First, navigate to the backend directory:
```bash
cd backend
```

Create a Python virtual environment:
```bash
python -m venv .venv
```

Activate the virtual environment:
- On Windows:
  ```bash
  .venv\Scripts\activate
  ```
- On macOS/Linux:
  ```bash
  source .venv/bin/activate
  ```

Install the required Python packages:
```bash
pip install -r requirements.txt
```

Create a `.env` file by copying the example:
```bash
# On Windows
copy .env.example .env

# On macOS/Linux
cp .env.example .env
```

**Edit the `.env` file** with your specific configuration, especially the `DATABASE_URL` and any necessary API keys (`GOOGLE_MAPS_KEY`, etc.).

### 2. Frontend Setup

Navigate to the frontend directory:
```bash
cd ../frontend
```

Install the required Node.js packages:
```bash
npm install
```

## Running the Application

### 1. Start the Backend

Make sure you are in the `backend` directory with the virtual environment activated. Run the FastAPI server:
```bash
uvicorn app.main:app --reload
```
The backend API will be running at `http://localhost:8000`.

### 2. Start the Frontend

In a **new terminal**, navigate to the `frontend` directory:
```bash
cd frontend
```

Run the React development server:
```bash
npm run dev
```
The frontend application will be available at `http://localhost:5173` (or another port if 5173 is busy).

## Building for Production

To create a production-ready build of the frontend, run the following command in the `frontend` directory:
```bash
npm run build
```
The optimized and minified files will be placed in the `frontend/dist` directory. These are the files you would deploy to a static file server (like Nginx or Vercel).
