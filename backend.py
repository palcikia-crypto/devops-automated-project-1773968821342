"""
Polymarket Lab - Simple Backend Server
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI(
    title="Polymarket Lab",
    description="Automated Prediction Market Trading Laboratory for Crypto Markets",
    version="1.5.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="dashboard"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - redirect to dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Polymarket Lab</title>
        <meta http-equiv="refresh" content="0; url=/dashboard/">
    </head>
    <body>
        <p>Redirecting to <a href="/dashboard/">dashboard</a>...</p>
    </body>
    </html>
    """

@app.get("/dashboard/", response_class=HTMLResponse)
async def dashboard():
    """Dashboard endpoint"""
    try:
        with open("dashboard/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Dashboard not found</h1><p>Please check the dashboard directory.</p>")

@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Polymarket Lab is running!",
        "version": "1.5.0"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
