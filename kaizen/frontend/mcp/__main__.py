from kaizen.frontend.mcp.mcp_server import mcp, app
import threading
import uvicorn
import logging

def run_api_server():
    """Run the FastAPI server for UI and API in a background thread."""
    try:
        # We run with log_level="warning" to avoid cluttering stdio for MCP
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
    except Exception as e:
        logging.error(f"Failed to start UI server: {e}")

def main():
    """
    Main entry point for the server.
    """
    # Start the HTTP API/UI server in a daemon thread so it dies when the parent dies
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()

    # Start FastMCP using stdio (which blocks)
    mcp.run()

if __name__ == "__main__":
    main()
