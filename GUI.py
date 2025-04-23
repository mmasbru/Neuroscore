import PySimpleGUI as sg 
import pandas as pd
import logging
from feature_extractor import main_features
from feature_extractor import regress_out_covariates, zscore_and_impute, compute_neuroscore


# --- GUI layout
layout = [
    [sg.Text("FreeSurfer dir"), sg.Input(key="path_fs"), sg.FolderBrowse()],
    [sg.Text("STRUCT dir"),      sg.Input(key="path_tab"), sg.FolderBrowse()],
    [sg.Text("Beta CSV"),        sg.Input(key="wd_beta"),   sg.FileBrowse(file_types=(("CSV","*.csv"),))],
    [sg.Text("Demo CSV (opt)"),  sg.Input(key="path_demo"), sg.FileBrowse(file_types=(("CSV","*.csv"),))],
    [sg.Text("Log file"),        sg.Input(key="log_path"),  sg.FileBrowse()],
    [sg.Button("Run"), sg.Exit()],
    [sg.Multiline(size=(80,20), key="output", autoscroll=True)]
]

window = sg.Window("Neuroscore GUI", layout)  # turn0search4

while True:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, "Exit"):
        break
    if event == "Run":
        # Setup logging
        logging.basicConfig(filename=values["log_path"], level=logging.INFO)
        window["output"].print("Starting neuroscore computation...")
        try:
            # 1) extract features + merge with demo
            df = main_features(values["path_fs"], values["path_tab"], values["path_demo"] or None)
            window["output"].print("Features extracted:", df.shape)
            # 2) regress out covariates
            dependent = [c for c in df.columns if c not in ["Age","Sex"]]
            res = regress_out_covariates(df.set_index("ID"), dependent)
            residuals_df = pd.concat(res, axis=1)
            window["output"].print("Covariates regressed out")
            # 3) z-score & impute
            zimp = zscore_and_impute(residuals_df)
            window["output"].print("Data z-scored & imputed")
            # 4) load beta & compute neuroscore
            beta = pd.read_csv(values["wd_beta"], index_col=0).astype(float).fillna(0)
            neuro = compute_neuroscore(zimp, beta)
            window["output"].print("Neuroscore computed:\n", neuro.head().to_string())
            # save results
            out_csv = values["path_tab"] + "/neuroscore_result.csv"
            neuro.to_csv(out_csv)
            window["output"].print(f"Results saved to {out_csv}")
        except Exception as e:
            window["output"].print("ERROR:", e)

window.close()