import os
import logging
import pandas as pd
import PySimpleGUI as sg
from feature_extractor import main

# --- Helper: setup logging (reuse existing logic) ---
def setup_logging(log_path):
    log_directory = os.path.dirname(log_path)
    if log_directory and not os.path.exists(log_directory):
        os.makedirs(log_directory)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )

# --- GUI Layout ---
layout = [
    [sg.Text("FreeSurfer dir"), sg.Input(key="path_fs"), sg.FolderBrowse()],
    [sg.Text("STRUCT dir"),      sg.Input(key="path_tab"), sg.FolderBrowse()],
    [sg.Text("Beta CSV"),        sg.Input(key="wd_beta"),   sg.FileBrowse(file_types=(("CSV","*.csv"),))],
    [sg.Text("Demo CSV (opt)"),  sg.Input(key="path_demo"), sg.FileBrowse(file_types=(("CSV","*.csv"),))],
    [sg.Text("Log file"),        sg.Input(key="log_path"),  sg.FileBrowse()],
    [sg.Button("Run"), sg.Exit()],
    [sg.Multiline(size=(80,20), key="output", autoscroll=True)]
]

window = sg.Window("Neuroscore GUI", layout)

# --- Event Loop ---
while True:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, "Exit"):
        break

    if event == "Run":
        # Setup logging to file and console
        setup_logging(values["log_path"] or "neuroscore.log")
        window["output"].print("Starting neuroscore pipeline...")

        try:
            # Call main() directly
            neuroscore = main(
                path_fs   = values["path_fs"],
                path_tab  = values["path_tab"],
                wd_beta   = values["wd_beta"],
                log_path  = values["log_path"],
                path_demo = values["path_demo"] or None
            )

            # Display results
            window["output"].print("Neuroscore computed:\n", neuroscore.head().to_string())

            # Save results to CSV in STRUCT directory
            out_csv = os.path.join(values["path_tab"], "neuroscore_result.csv")
            neuroscore.to_csv(out_csv)
            window["output"].print(f"Results saved to {out_csv}")

        except Exception as e:
            window["output"].print("ERROR during execution:\n", e)

window.close()