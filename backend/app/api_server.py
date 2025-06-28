"""
FastAPI server entry point for the MediCapital Lead API
Run with: uvicorn backend.app.api_server:app --reload --host 0.0.0.0 --port 8000
"""

import os
from .api.main import app

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
