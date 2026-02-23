from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static
from textual.containers import Container, VerticalScroll
from textual.binding import Binding
from textual.reactive import reactive

import subprocess
import os

class History(VerticalScroll):
    """Zone d'historique des commandes"""

    def add_entry(self, text: str):
        self.mount(Static(text))

class CommandApp(App):

    CSS = """
    Screen {
        layout: vertical;
    }

    #history {
        height: 1fr;
        border: solid white;
        padding: 1;
    }

    #input {
        dock: bottom;
    }
    """

    current_dir = reactive("")

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quitter"),
        Binding("ctrl+l", "clear", "Clear")
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        yield Container(
            History(id="history"),
        )

        yield Input(placeholder="Tape ta commande...", id="input")

        yield Footer()

    def watch_current_dir(self, new_dir: str):
        input_widget = self.query_one("#input", Input)

        display_path = new_dir
        input_widget.placeholder = f"{display_path} ❯"

    def on_mount(self):
        self.current_dir = os.getcwd()

    def on_input_submitted(self, event: Input.Submitted):
        command = event.value

        history = self.query_one("#history", History)
        history.add_entry(f"> {command}")

        event.input.value = ""

        self.handle_command(command)

    def handle_command(self, command: str):
        history = self.query_one("#history", History)

        if command == "ls":
            history.add_entry("test")
            return

        if command == "clear":
            history.remove_children()
            return

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.current_dir
            )

            if result.stdout:
                history.add_entry(result.stdout.strip())

            if result.stderr:
                history.add_entry(f"[red]{result.stderr.strip()}[/red]")

        except Exception as e:
            history.add_entry(f"[red]Erreur : {e}[/red]")

    def action_clear(self):
        self.query_one("#history").remove_children()

if __name__ == "__main__":
    CommandApp().run()