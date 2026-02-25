from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static
from textual.containers import Container, VerticalScroll
from textual.binding import Binding
from textual.reactive import reactive

import subprocess
import os
import json

VARS = {
    "CURRENT_DISK": os.path.splitdrive(os.getcwd())[0],
}

def vars_path(path) -> str:
    for var in VARS:
        path = path.replace(var, VARS[var])
    return path

class PathVariables:
    """Stocke les chemin vers des fichiers dans un fichier json"""
    def __init__(self, path="path.json"):
        self.path = path
    
    def is_variable(self, var:str) -> bool:
        """Renvoie True si le fichier path contient une variable pour var"""
        return var in self.variables
    
    def add(self, name, path):
        new = self.variables
        new[name] = path
        with open(self.path, "w") as f:
            json.dump(new, f)

    @property
    def variables(self):
        with open(self.path, "r") as f:
            variables = json.load(f)
        return variables

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
        command.strip()
        els = command.split(" ")
        path_variables = PathVariables()

        if command == "ls":
            command = "dir /B"

        if els[0] == "cd":
            path = els[1]
            result_path = os.path.normpath(os.path.join(self.current_dir, path))
            if os.path.exists(result_path):
                if os.path.isdir(result_path):
                    self.current_dir = result_path
                    return
                history.add_entry(f"[red]Déplacement vers un fichier impossible[/red]")
            else:
                history.add_entry(f"[red]Chemin {result_path} non valide[/red]")
        elif els[0] == "vars":
            for name, value in VARS.items():
                history.add_entry(f"{name} {value}")
            return
        elif els[0] == "custom":
            if len(els) == 1:
                history.add_entry(f"[red]Aucun argument donné[/red]")
                return
            
            if els[1] == "path":
                if len(els) != 4:
                    history.add_entry(f"[red]Assurez vous d'utiliser `custom path chemin raccourci`[/red]")
                    return
                
                path = vars_path(els[2])
                result_path = os.path.normpath(os.path.join(self.current_dir, path))
                if not os.path.exists(result_path):
                    history.add_entry(f"[red]{vars_path(result_path)} n'existe pas.[/red]")
                    return
                history.add_entry(f"[yellow]{path} {els[2]} n'existe pas.[/yellow]")
                path_variables.add(els[3], result_path if path == els[2] else path)
                return

        if path_variables.is_variable(els[0]):
            els[0] = vars_path(path_variables.variables[els[0]])
            command = " ".join(els)

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