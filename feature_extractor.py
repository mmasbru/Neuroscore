import os
import pandas as pd

# Define input and output paths.
path_in = '/home/mireia/Desktop/01_PROJECTS/03_Neuroscore/01_DATA/FS/'
path_out = '/home/mireia/Desktop/01_PROJECTS/03_Neuroscore/01_DATA/STRUCT/'
os.environ["SUBJECTS_DIR"] = path_in

# Get a list of subject directories in path_in
files = [f for f in os.listdir(path_in) if os.path.isdir(os.path.join(path_in, f))]
files_in = ' '.join(files)

#Measures to compute.
def get_aseg(files_in, path_out):
    file_out = os.path.join(path_out, f'aseg_volume.txt')
    cmd = f'asegstats2table --subjects {files_in} --meas volume --tablefile {file_out}'
    os.system(cmd)

def get_aparc(files_in, path_out):
    aparc_meas = ['volume', 'area', 'thickness', 'thicknessstd','meancurv', 'foldind', 'curvind']
    hemis = ['rh', 'lh']
    for meas in aparc_meas:
        for hemi in hemis:
            file_out = os.path.join(path_out, f'aparc_{meas}_{hemi}.txt')
            cmd = f'aparcstats2table --hemi {hemi} --subjects {files_in} --parc aparc --tablefile {file_out} --meas {meas}'
            os.system(cmd)

def merge_all(path_out):
    output_file = os.path.join(path_out, 'combined_data.csv')
    if os.path.exists(output_file):
        print('Merging already done!')
        return

    txt_files = [f for f in os.listdir(path_out) if f.endswith('.txt')]
    dfs = []

    for file in txt_files:
        file_path = os.path.join(path_out, file)
        df = pd.read_csv(file_path, sep='\t')  # Change 'sep' if needed
        dfs.append(df)
    combined_df = pd.concat(dfs, axis=1)
    combined_df = combined_df.loc[:, ~combined_df.columns.duplicated(keep='last')]
    combined_df.to_csv(output_file, index=False)
    print(f"Combined CSV file saved at: {output_file}")


get_aseg(files_in, path_out)
get_aparc(files_in, path_out)
merge_all(path_out)

