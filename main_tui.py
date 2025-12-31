import sys
from asyncio import CancelledError
from tui.app import AgentApp

if __name__ == "__main__":
    try:
        app = AgentApp()
        app.run()
    except (KeyboardInterrupt, CancelledError, SystemExit):
        sys.exit(0)
