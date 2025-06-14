"""
FastAPI server entry point for the MediCapital Lead API
Run with: uvicorn backend.app.api_server:app --reload --host 0.0.0.0 --port 8000
"""

from .api.main import app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
