from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Collapsible, Static
from rich.syntax import Syntax

class CollapsibleApp(App):
    CSS = """
    Screen {
        background: #1e1e1e;
    }
    
    Header {
        background: #2d2d2d;
        color: #cccccc;
    }
    
    Footer {
        background: #2d2d2d;
        color: #cccccc;
    }
    
    Vertical {
        height: auto;
    }
    
    Collapsible {
        width: 100%;
        height: auto;
        background: #1e1e1e;
        border: tall #3e3e3e;
        margin: 0 0 1 0;
    }
    
    Collapsible > CollapsibleTitle {
        background: #2d2d2d;
        color: #cccccc;
        padding: 0 2;
        height: 3;
    }
    
    Collapsible > CollapsibleTitle:hover {
        background: #3e3e3e;
    }
    
    Collapsible.-collapsed > CollapsibleTitle {
        background: #2d2d2d;
    }
    
    Collapsible > Contents {
        background: #1e1e1e;
        padding: 1 2;
        height: auto;
    }
    
    Static {
        background: #1e1e1e;
        color: #cccccc;
        height: auto;
    }
    
    .info-text {
        color: #888888;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        
        yield Static("model: gpt-4-turbo    directory: ~/Developer/project", classes="info-text")
        
        # Example 1: Quick function
        code1 = '''def greet(name):
    return f"Hello, {name}!"

print(greet("World"))'''
        
        syntax1 = Syntax(
            code1,
            "python",
            theme="monokai",
            line_numbers=False,
            word_wrap=False,
            background_color="#1e1e1e"
        )
        
        yield Collapsible(
            Static(syntax1),
            title="▸ Example: Simple greeting function",
            collapsed=True
        )
        
        # Example 2: More complex code
        code2 = '''def fibonacci(n):
    """Generate Fibonacci sequence up to n terms."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    result = [0, 1]
    while len(result) < n:
        result.append(result[-1] + result[-2])
    
    return result

# Usage
fib_numbers = fibonacci(10)
print(f"First 10: {fib_numbers}")
print(f"Sum: {sum(fib_numbers)}")'''
        
        syntax2 = Syntax(
            code2,
            "python",
            theme="monokai",
            line_numbers=True,
            word_wrap=False,
            background_color="#1e1e1e"
        )
        
        yield Collapsible(
            Static(syntax2),
            title="▸ Example: Fibonacci generator with validation",
            collapsed=True
        )
        
        # Example 3: Class example
        code3 = '''class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def multiply(self, a, b):
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

calc = Calculator()
calc.add(5, 3)
calc.multiply(4, 7)'''
        
        syntax3 = Syntax(
            code3,
            "python",
            theme="monokai",
            line_numbers=True,
            word_wrap=False,
            background_color="#1e1e1e"
        )
        
        yield Collapsible(
            Static(syntax3),
            title="▸ Example: Calculator class with history",
            collapsed=True
        )
        
        yield Static("\n100% context left · ? for shortcuts", classes="info-text")
        yield Footer()

if __name__ == "__main__":
    app = CollapsibleApp()
    app.run()