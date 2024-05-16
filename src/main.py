# -*- coding: utf-8 -*-
"""
main.py - part of the h4cui project

This module provides the main application for the h4cui project.  It provides a GUI for selecting physical ports and
CNC ports and running the hub4com utility to replicate data between them.

Classes:
    Hub4ComApp: The main application class for the h4cui project.

Entry Point:
    main: The main entry point for the h4cui project.

Example Usage:
    python main.py

This is free software licensed under the BSD 3-Clause License (see LICENSE file for details).
"""
import subprocess
import os
import threading
import tkinter as tk
from tkinter import Checkbutton, Radiobutton, StringVar, filedialog, Label, ttk
from cnc_ports import CNCPortUtil
from typing import List, Tuple, Optional, Any


DEFAULT_HUB4COM_PATH = "C:\\Program Files (x86)\\com0com\\hub4com.exe"
BAUD_RATES: Tuple[int, ...] = (
    300,
    1200,
    2400,
    4800,
    9600,
    14400,
    19200,
    38400,
    57600,
    115200,
)
DEFAULT_BAUD = 115200


class Hub4ComApp(tk.Tk):
    """The Hub4Com application.

    Attributes:
        baud: A tk.StringVar representing the baud rate.
        external_padx: An integer representing the external padding in the x direction.
        external_pady: An integer representing the external padding in the y direction.
        hub4com_path: A string representing the path to the hub4com executable.
        hub4com_path_label: A tk.Label representing the label for the hub4com path.
        internal_padx: An integer representing the internal padding in the x direction.
        internal_pady: An integer representing the internal padding in the y direction.
        ports: A CNCPortUtil representing the CNC ports.
        process: A subprocess.Popen representing the process running the hub4com executable.
        replica_ports: A list of tk.StringVar representing the replica ports.
        source_port: A tk.StringVar representing the source port.
    """

    def __init__(self, ports: CNCPortUtil) -> None:
        """Initializes the Hub4ComApp with the given ports.

        Args:
            ports: A CNCPortUtil instance
        """
        super().__init__()
        self.baud: StringVar = StringVar()
        self.baud.set(str(DEFAULT_BAUD))
        self.external_padx: int = 10
        self.external_pady: int = 4
        self.hub4com_path: str = DEFAULT_HUB4COM_PATH
        self.hub4com_path_label: Optional[Label] = None
        self.internal_padx: int = 2
        self.internal_pady: int = 2
        self.ports: CNCPortUtil = ports
        self.process: Optional[subprocess.Popen] = None
        self.replica_ports: List[StringVar] = []
        self.source_port: StringVar = StringVar()

        self._init_ui()

    def _init_ui(self) -> None:
        """Initializes the user interface."""
        self.title("H4CUI - Hub4Com UI by KJ5DTV")
        self.iconbitmap("assets/kj5dtv.ico")
        self.geometry("1024x768")
        self.grid_columnconfigure(
            0, weight=1
        )  # Set a minimum width for the first column
        self.grid_columnconfigure(
            1, weight=2
        )  # Set a minimum width for the second column
        self.grid_rowconfigure(5, weight=1)
        self._create_port_frame()
        self._create_instructions()
        self._create_hub4com_path_elements()
        self._create_physical_ports()
        self._create_cnc_ports()
        self._create_command_label()
        self._create_baud_rate_dropdown()
        self._create_status_text()
        self._create_buttons()

    def _create_port_frame(self) -> None:
        """Creates the port frame in the user interface."""
        self.port_frame = tk.LabelFrame(self, text="Port Selection")
        self.port_frame.grid_columnconfigure(0, weight=1)
        self.port_frame.grid_columnconfigure(1, weight=2)
        self.instructions = tk.Label(
            master=self.port_frame,
            text="Select a physical port to replicate to one or more CNC ports.",
            padx=self.internal_padx,
            pady=self.internal_pady,
            anchor="w",  # Align the text to the left
        )
        self.instructions.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=self.internal_padx,
            pady=self.internal_pady,
        )
        self.port_frame.grid(
            row=0,
            column=0,
            rowspan=3,
            sticky="ew",
            padx=self.external_padx,
            pady=self.external_pady,
        )

    def _create_physical_ports(self) -> None:
        """Creates the physical ports in the user interface."""
        self.radio_frame = tk.LabelFrame(
            self.port_frame,
            text="Physical Ports",
            padx=self.internal_padx,
            pady=self.internal_pady,
        )
        self.radio_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=self.internal_padx,
            pady=self.internal_pady,
        )

        _sorted_physical_ports: List[Any] = sorted(
            self.ports.physical_ports, key=lambda port: port.port_name
        )

        self.source_port: tk.StringVar = (
            tk.StringVar()
        )  # Create a StringVar for the Radiobutton widgets

        first_available_port: Any | None = next(
            (port for port in _sorted_physical_ports if not port.is_in_use), None
        )

        self.source_port.set(
            first_available_port.port_name if first_available_port else ""
        )

        for i, com_port in enumerate(_sorted_physical_ports):
            in_use: bool = com_port.is_in_use
            status_text: str = "- in use" if in_use else " - not in use"
            state: str = "disabled" if in_use else "normal"

            Radiobutton(
                master=self.radio_frame,
                value=com_port.port_name,  # Set the value option to a unique value
                variable=self.source_port,  # Use the same StringVar for all the Radiobutton widgets
                state=state,
            ).grid(row=i, column=0, sticky="nw")

            Label(
                master=self.radio_frame,
                text=com_port.port_name,
            ).grid(row=i, column=1, sticky="nw")

            Label(
                master=self.radio_frame,
                text=status_text,
                font=("TkDefaultFont 10 italic"),  # Set the font option to italic
            ).grid(row=i, column=2, sticky="nw")

    def _create_cnc_ports(self) -> None:
        """Creates the com0com radio buttons in the user interface."""
        self.check_frame = tk.LabelFrame(
            master=self.port_frame,
            text="CNC Ports",
            padx=self.internal_padx,
            pady=self.internal_pady,
        )
        self.check_frame.grid(
            row=1,
            column=1,
            sticky="nsew",
            padx=self.internal_padx,
            pady=self.internal_pady,
        )
        for i, (primary_port, secondary_port) in enumerate(self.ports.cnc_port_pairs):
            in_use = primary_port.is_in_use
            status_text = "- in use" if in_use else "- not in use"
            replicates_to_text: str = (
                f" (replicates to {secondary_port.port_name})" if secondary_port else ""
            )
            state = "disabled" if in_use else "normal"
            var = StringVar(value=primary_port.port_name if not in_use else "")
            self.replica_ports.append(var)
            Checkbutton(
                master=self.check_frame,
                variable=var,
                onvalue=primary_port.port_name,
                offvalue="",
                state=state,
            ).grid(row=i % 6, column=i // 6 * 3, sticky="nw")
            Label(
                master=self.check_frame,
                text=f"{primary_port.port_name}{replicates_to_text}",
            ).grid(row=i % 6, column=i // 6 * 3 + 1, sticky="nw")
            Label(
                master=self.check_frame,
                text=status_text,
                font=("TkDefaultFont", 10, "italic"),  # Set the font option to italic
            ).grid(row=i % 6, column=i // 6 * 3 + 2, sticky="nw")

    def _create_instructions(self) -> None:
        """Creates the instructions in the user interface."""
        self.instructions_frame = tk.LabelFrame(
            self, text="Info", padx=self.external_padx, pady=self.external_pady
        )
        self.instructions_frame.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=self.internal_padx,
            pady=self.internal_pady,
        )
        self.instructions_frame.grid_columnconfigure(0, weight=1)

        instructions_text = (
            "This is a UI wrapper for the hub4com application, part of the com0com suite by Vyacheslav Frolov.\n"
            "Download and configure com0com from https://com0com.sourceforge.net/.\n\n"
            "Select a physical port to replicate to one or more com0com ports (CNC ports).\n"
            "Select the baud rate, the location of the hub4com executable, and press 'Run'."
        )

        self.instructions_label = tk.Label(
            self.instructions_frame, text=instructions_text, anchor="nw", justify="left"
        )
        self.instructions_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=self.internal_padx,
            pady=self.internal_pady,
        )

    def _create_hub4com_path_elements(self) -> None:
        """Creates the hub4com browse to the location of hub4com in the UI thingy."""
        self.hub4com_path_frame = tk.LabelFrame(
            self, text="Hub4Com Path", padx=self.external_padx, pady=self.external_pady
        )
        self.hub4com_path_frame.grid(
            row=1,
            column=1,
            columnspan=1,
            sticky="sew",
            padx=self.internal_padx,
            pady=self.internal_pady,
        )
        self.hub4com_path_frame.grid_columnconfigure(
            0, weight=1
        )  # Set the weight of the first column to 1
        self.hub4com_path_frame.grid_columnconfigure(
            1, weight=0
        )  # Set the weight of the second column to 0

        self.hub4com_path_label = tk.Label(
            self.hub4com_path_frame, text=self.hub4com_path, anchor="nw"
        )
        self.hub4com_path_label.grid(
            row=0,
            column=0,
            padx=self.internal_padx,
            pady=self.internal_pady,
            sticky="ew",
        )

        self.hub4com_path_button = tk.Button(
            self.hub4com_path_frame,
            text="Browse",
            command=self.browse_hub4com_path,
            padx=self.internal_padx,
            pady=self.internal_pady,
            anchor="ne",
        )
        self.hub4com_path_button.grid(
            row=0,
            column=1,
            padx=self.internal_padx,
            pady=self.internal_pady,
            sticky="e",
        )

    def _create_baud_rate_dropdown(self) -> None:
        """Creates the baud ddl"""
        self.baud_rate_frame = tk.LabelFrame(
            self, text="Baud Rate", padx=self.external_padx, pady=self.external_pady
        )
        self.baud_rate_frame.grid(
            row=2,
            column=1,
            columnspan=1,
            sticky="sew",
            padx=self.internal_padx,
            pady=self.internal_pady,
        )

        self.baud_rate_frame.grid_columnconfigure(0, weight=1)
        self.baud_rate_frame.grid_columnconfigure(1, weight=2)

        self.baud_rate_label = tk.Label(
            self.baud_rate_frame, text="Select baud rate:", anchor="e"
        )
        self.baud_rate_label.grid(
            row=0,
            column=0,
            sticky="e",
            padx=self.internal_padx,
            pady=self.internal_pady,
        )

        self.baud_rate_dropdown = ttk.Combobox(
            self.baud_rate_frame, textvariable=self.baud, state="readonly"
        )
        self.baud_rate_dropdown["values"] = BAUD_RATES
        self.baud_rate_dropdown.bind("<<ComboboxSelected>>", self.update_baud)
        self.baud_rate_dropdown.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=self.internal_padx,
            pady=self.internal_pady,
        )

    def _create_command_label(self) -> None:
        """Creates the command label"""
        self.command_label = tk.Text(self, height=3, wrap=tk.WORD, font=("Courier", 8))
        self.command_label.grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=self.external_padx,
            pady=self.external_pady,
        )
        self.command_label.insert(tk.END, "hub4com command will appear here.")

    def _create_status_text(self) -> None:
        """Creates the status text"""
        self.status_text = tk.Text(self, height=10, font=("Courier", 8))
        self.status_text.grid(
            row=5,
            column=0,
            columnspan=2,
            sticky="nsew",
            padx=self.external_padx,
            pady=self.external_pady,
        )
        self.status_text.insert(tk.END, "hub4com status will appear here.")

    def _create_buttons(self) -> None:
        """Creates the buttons at the bottom of the UI"""
        self.button_frame = tk.Frame(self)
        self.button_frame.grid(
            row=6,
            column=0,
            columnspan=2,
            sticky="s",
            padx=self.external_padx,
            pady=self.external_pady,
        )
        self.run_button = tk.Button(
            self.button_frame,
            text="Run",
            command=self.run_command,
            padx=self.external_padx,
            pady=self.external_pady,
        )
        self.run_button.grid(
            row=0, column=0, padx=self.internal_padx, pady=self.internal_pady
        )
        self.stop_button = tk.Button(
            self.button_frame,
            text="Stop",
            command=self.stop_command,
            padx=self.external_padx,
            pady=self.external_pady,
        )
        self.stop_button.grid(
            row=0, column=1, padx=self.internal_padx, pady=self.internal_pady
        )
        self.exit_button = tk.Button(
            self.button_frame,
            text="Exit",
            command=self.exit_command,
            padx=self.external_padx,
            pady=self.external_pady,
        )
        self.exit_button.grid(
            row=0, column=2, padx=self.internal_padx, pady=self.internal_pady
        )

    def run_command(self) -> None:
        """This method runs the hub4com command in a separate thread."""
        threading.Thread(target=self._run_command).start()

    def _run_command(self) -> None:
        """This method runs the hub4com command."""
        self.status_text.delete("1.0", tk.END)

        source = self.source_port.get()
        replicas: List[str] = [p.get() for p in self.replica_ports if p.get()]
        command: List[str] = self.get_hub4com_command(source, replicas)
        self.update_command(command)
        self.process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        self.update_status("Hub4Com process started.\n\n")
        if self.process is not None and self.process.stdout is not None:
            for line in iter(self.process.stdout.readline, b""):
                self.update_status(line.decode())
            try:
                self.process.wait()
            except AttributeError:
                pass
        self.update_status("Hub4Com process terminated.")

    def browse_hub4com_path(self) -> None:
        """Opens a file dialog to browse to the hub4com executable."""
        initial_dir = (
            os.path.dirname(self.hub4com_path)
            if os.path.exists(self.hub4com_path)
            else "/"
        )
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir, filetypes=[("Executable files", "*.exe")]
        )
        if file_path:
            self.hub4com_path = file_path
            if self.hub4com_path_label is not None:
                self.hub4com_path_label.config(text=self.hub4com_path)

    def update_baud(self, event) -> None:
        """Updates the baud rate when the dropdown selection changes."""
        self.baud.set(self.baud_rate_dropdown.get())

    def stop_command(self) -> None:
        """Kills the hub4com process."""
        if self.process is not None:
            self.process.terminate()
            self.process = None
            self.update_status(line="Hub4Com process terminated.")

    def exit_command(self) -> None:
        """Kills exits the application."""
        self.destroy()

    def update_status(self, line) -> None:
        """Updates the status text with the given line."""
        self.status_text.insert(index=tk.END, chars=line)
        self.status_text.see(index=tk.END)

    def update_command(self, command) -> None:
        """Updates the command label with the command."""
        self.command_label.delete(index1="1.0", index2=tk.END)
        self.command_label.insert(index=tk.END, chars=" ".join(command))
        self.command_label.see(index=tk.END)

    def get_hub4com_command(self, source, replicas) -> List[str]:
        """Formats the hub4com command with the given source and replica ports."""
        return [
            self.hub4com_path,
            "--octs=off",
            f"--baud={self.baud.get()}",  # Call get() on self.baud
            "--bi-route=0:All",
            f"\\\\.\\{source}",
        ] + [f"\\\\.\\{p}" for p in replicas]


def main() -> None:
    """Welcome to the main function! Woo..."""
    ports = CNCPortUtil()
    h4 = Hub4ComApp(ports)
    h4.mainloop()


if __name__ == "__main__":
    main()
