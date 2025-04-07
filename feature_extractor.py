import os
import pandas as pd

def get_files(path_in, log_file):
    # List all the subject directories
    files = [f for f in os.listdir(path_in) if os.path.isdir(os.path.join(path_in, f))]
    
    # The required files for asegstats2table and aparcstats2table
    required_files = {
        'aseg': 'stats/aseg.stats',
        'aparc_lh': 'stats/lh.aparc.stats',
        'aparc_rh': 'stats/rh.aparc.stats'
    }

    # List to hold valid subjects
    valid_subjects = []
    
    # Open log file to record missing files
    with open(log_file, 'w') as log:
        log.write('Missing Files Log\n')

        for subject in files:
            subject_path = os.path.join(path_in, subject)
            missing = False
            
            # Check if all the required files exist for this subject
            for file_key, file_path in required_files.items():
                full_file_path = os.path.join(subject_path, file_path)
                if not os.path.exists(full_file_path):
                    missing = True
                    log.write(f"Subject: {subject}, Missing file: {file_path}\n")
            
            # If all required files exist, add subject to valid_subjects list
            if not missing:
                valid_subjects.append(subject)
    
    return valid_subjects
        
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
        df = pd.read_csv(file_path, sep='\t')
        df.index = df.iloc[:, 0]
        df = df.drop(df.columns[0], axis=1)
        dfs.append(df)
        
    combined_df = pd.concat(dfs, axis=1, join='outer')
    combined_df = combined_df.loc[:, ~combined_df.columns.duplicated(keep='last')]
    combined_df.to_csv(output_file, sep=',', decimal='.', index=True)
    print(f"Combined CSV file saved at: {output_file}")
    
    
def main(path_in, path_out):
    os.environ["SUBJECTS_DIR"] = path_in
    log_file = os.path.join(path_out, 'log.txt')
    files = get_files(path_in, log_file)
    files_in = ' '.join(files)
    
    get_aseg(files_in, path_out)
    get_aparc(files_in, path_out)
    merge_all(path_out)


path_in = '/home/mireia/Desktop/01_PROJECTS/05_Espectro/FS'
path_out = '/home/mireia/Desktop/01_PROJECTS/05_Espectro/STRUCT'
main(path_in, path_out)