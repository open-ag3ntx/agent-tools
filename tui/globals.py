from textual.app import App
from typing import Optional

_app: Optional[App] = None

def set_app(app: App) -> None:
    global _app
    _app = app

def get_app() -> App:
    if _app is None:
        raise RuntimeError("App not initialized")
    return _app
