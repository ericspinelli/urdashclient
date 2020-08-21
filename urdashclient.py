"""
Client software to connect to UR Dashboard Server

GUI for connecting to UR Dashboard Server (Port 29999) to operate a UR robot remotely.
The Dashboard Server allows high level operations such as Load, Play, Stop, etc.
e-Series commands: https://www.universal-robots.com/articles/ur/dashboard-server-e-series-port-29999/
CB-Series commands: https://www.universal-robots.com/articles/ur/dashboard-server-cb-series-port-29999/
"""

# encoding: utf-8

__version__ = '0.7'
__author__ = 'Eric Spinelli'

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from os.path import commonprefix
import socket

class FileMenu(tk.Menu):
    # File menu at top of window (Save log, About, Quit)
    def __init__(self, parent, controller, *args, **kwargs):
        tk.Menu.__init__(self, parent, *args, **kwargs)

        # controller is root = tk.Tk()
        self.controller = controller

        self.add_command(label="Save Log", command=self.save_log)
        self.add_command(label="About", command=self.about)
        self.add_separator()
        self.add_command(label="Quit", command=self.quit)

    def save_log(self):
        directory = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=(("text files", "*.txt"), ("all files", "*.*")))
        if directory:
            f = open(directory, "w+")
            f.write(self.controller.log.output_text.get("1.0", tk.END))
            f.close()

    def about(self):
        msg = """UR Test Dashboard Client version 0.7 Beta
Created by ESP @ URJP

This client was developed for test purposes only.
It is provided as is.

Universal Robots takes no responsibility for this software."""
        messagebox.showinfo("About", msg)

    def quit(self):
        self.controller.parent.destroy()
        quit()

    def close(self):
        self.top.destroy()

class IPWindow(tk.Frame):
    # Frame for IP address, Port # (locked), and connect/disconnect buttons
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.config(width=100, padx=5, pady=5, borderwidth=2, relief="groove")

        # Create widgets
        self.ip_label = tk.Label(self, text="Robot IP Address:", font=("Arial", 12), width=14, anchor="e")
        self.ip_entry = tk.Entry(self, font=("Arial", 12), width=35)
        self.connect_button = tk.Button(self, text="Connect", font=("Arial", 12), width=9, padx=2, pady=2, command=self.parent.connect)
        self.disconnect_button = tk.Button(self, text="Disconnect", font=("Arial", 12), width=9, padx=2, pady=2, state="disabled", command=self.parent.disconnect)
        self.port_label = tk.Label(self, text="Port:", font=("Arial", 12), width=14, anchor="e")
        self.port_entry = tk.Entry(self, font=("Arial", 12), width=35)

        # Initialize widgets
        self.ip_entry.insert(0, "0.0.0.0")
        self.ip_entry.bind('<Return>', self.keyboard_handler_return)
        self.port_entry.insert(0, "29999")
        self.port_entry.config(state="disabled")

        # Place widgets
        self.ip_label.grid(row=0, column=0)
        self.ip_entry.grid(row=0, column=1)
        self.connect_button.grid(row=0, column=2)
        self.port_label.grid(row=1, column=0)
        self.port_entry.grid(row=1, column=1)
        self.disconnect_button.grid(row=1, column=2)

    def keyboard_handler_return(self, event=None, *args):
        if self.connect_button['state'] == tk.NORMAL:
            self.parent.connect()

class LogWindow(tk.Frame):
    # Frame for displaying commands sent by user and response from UR Dashboard Server
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.config(padx=5, pady=5)

        # Create widgets
        self.output_text = tk.Text(self, font=("Arial", 12), width=60, height=30, state="disabled")
        self.output_scroll = tk.Scrollbar(self, command=self.output_text.yview)

        # Configure widgets
        self.output_text.tag_config("send", foreground="green")
        self.output_text.tag_config("recv", foreground="blue")
        self.output_text['yscrollcommand'] = self.output_scroll.set

        # Place widgets
        self.output_text.grid(row=0, column=0)
        self.output_scroll.grid(row=0, column=1, sticky="nse")

class CommandWindow(tk.Frame):
    # Frame for command entry and send button
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.config(padx=5, pady=5, borderwidth=2, relief="groove")

        # Create widgets
        self.input_label = tk.Label(self, text="Command:", font=("Arial", 12), width=9, anchor="e")
        self.input_entry = tk.Entry(self, font=("Arial", 12), width=29)
        self.input_button = tk.Button(self, text="Send", font=("Arial", 12), width=9, padx=2, pady=2, command=self.parent.send)
        self.command_var = tk.StringVar()
        self.dashboard_commands = ["", "load ", "play", "pause", "stop", "robotmode", "safetystatus", "power on", "brake release", "power off"]
        self.dashboard_commands_full = ["load ", "play", "stop", "pause", "quit", "shutdown", "running", "robotmode", "get loaded program",
                                        "popup ", "close popup", "addtolog ", "isprogramsaved", "programstate", "polyscopeversion", "set operational mode",
                                        "clear operational mode", "power on", "power off", "brake release", "unlock protective stop", "close safety popup",
                                        "load installation ", "restart safety", "safetystatus", "get operational mode", "is in remote control",
                                        "get serial number", "get robot model"]

        self.command_list = tk.OptionMenu(self, self.command_var, *self.dashboard_commands, command=self.insert_cmd)

        # Configure widgets
        self.input_button.config(state="disabled")
        self.command_list.config(width=10, anchor=tk.W)
        self.input_entry.bind("<Return>", self.keyboard_handler_return)
        self.input_entry.bind("<Tab>", self.keyboard_handler_tab)

        # Place widgets
        self.input_label.grid(row=0, column=0)
        self.input_entry.grid(row=0, column=1)
        self.input_button.grid(row=0, column=3)
        self.command_list.grid(row=0, column=2)

    def insert_cmd(self, cmd):
        self.input_entry.delete(0, "end")
        self.input_entry.insert("insert", cmd)

    def keyboard_handler_return(self, event=None, *args):
        if self.input_button['state'] != tk.DISABLED:
            self.parent.send()
        else:
            messagebox.showinfo("Warning", "Command not sent. Not connected.")

    def keyboard_handler_tab(self, event=None, *args):
        substring = str.lower(self.input_entry.get())
        if substring != '':
            result = [cmd for cmd in self.dashboard_commands_full if cmd.startswith(substring)]
            if len(result) > 1:
                self.insert_cmd(commonprefix(result))
            elif len(result) == 1:
                self.insert_cmd(result[0])
            self.input_entry.icursor(tk.END)
            # Break bind propagation that would call Entry class default bind which moves cursor to a different widget
            return "break"

class MainApp(tk.Frame):
    # Main frame that contains all other frames and acts as go-between for class methods that must access data stored in other classes (frames)
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.menubar = tk.Menu(self, font=("Arial", 20))
        self.filemenu = FileMenu(self.menubar, self, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.parent.config(menu=self.menubar)

        self.ip = IPWindow(self)
        self.log = LogWindow(self)
        self.cmd = CommandWindow(self)

        self.ip.grid(row=0, column=0, padx=5, pady=5)
        self.log.grid(row=1, column=0, padx=5, pady=5)
        self.cmd.grid(row=2, column=0, padx=5, pady=5)

        self.BUFFER_SIZE = 4096
        self.socket = None

    def new_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s

    def connect(self):
        if self.socket is None:
            HOST = self.ip.ip_entry.get()
            PORT = int(self.ip.port_entry.get())

            self.socket = self.new_socket()

            try:
                self.socket.connect((HOST, PORT))
                self.write_text("Connecting to {}:{}\n".format(HOST, PORT))
                self.write_text(self.recv() + '\n', "recv")

                self.ip.connect_button.config(state="disabled")
                self.ip.disconnect_button.config(state="normal")
                self.cmd.input_button.config(state="normal")
            except TimeoutError as errmsg:
                self.disconnect()
                messagebox.showinfo("Error", errmsg)


    def disconnect(self):
        if self.socket != None:
            self.socket.close()
        self.socket = None

        self.write_text("Client has disconnected from server\n\n")
        self.ip.connect_button.config(state="normal")
        self.ip.disconnect_button.config(state="disabled")
        self.cmd.input_button.config(state="disabled")

    def send(self):
        if self.cmd.input_entry.get() != '':
            cmd = str(self.cmd.input_entry.get()) + '\n'
            self.write_text(cmd, "send")
            self.cmd.input_entry.delete(0, "end")

            self.socket.send(cmd.encode('utf-8'))
            self.write_text(self.recv() + '\n', "recv")

    def recv(self):
        return self.socket.recv(self.BUFFER_SIZE).decode('utf-8')

    def write_text(self, str, tag=None):
        self.log.output_text.config(state="normal")
        if tag == "send":
            str = "COMMAND: " + str
        elif tag == "recv":
            str = "REPONSE: " + str
        self.log.output_text.insert("insert", str, tag)
        self.log.output_text.config(state="disabled")
        self.log.output_text.see(tk.END)


def main():
    root = tk.Tk()
    root.title("UR Test Dashboard Client")
    try:
        root.iconbitmap("ur.ico")
    except:
        pass

    mainapp = MainApp(root)
    mainapp.pack(side="top", fill="both", expand=True)
    root.mainloop()

if __name__ == "__main__":
    main()

