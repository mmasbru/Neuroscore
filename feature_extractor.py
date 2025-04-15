import os
import subprocess
import pandas as pd


def get_files(path_in, log_file):
    # List all the subject directories
    files = [f for f in os.listdir(path_in) if os.path.isdir(os.path.join(path_in, f))]
    
    # The required files for asegstats2table and aparcstats2table
    required_files = {
        'aseg': 'stats/aseg.stats',
        'aparc_lh': 'stats/lh.aparc.stats',
        'aparc_rh': 'stats/rh.aparc.stats', 
        'lh.pial.T1': 'surf/lh.pial.T1',
        'rh.pial.T1': 'surf/rh.pial.T1',
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
            for _, file_path in required_files.items():
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

def get_surface_area(surface_file):
    try:
        result = subprocess.run(['mris_info', surface_file], capture_output=True, text=True, check=True)
        for line in result.stdout.split('\n'):
            if 'total_area' in line:
                res = float(line.split()[-1])
                return res  # Extract the numerical value
    except Exception as e:
        print(f"Error processing {surface_file}: {e}")
    return 0.0

def save_surface_areas_to_txt(surface_areas, output_file):
    with open(output_file, 'w') as f:
        f.write("subject\tpial\n")
        
        for subject, area in surface_areas.items():
            f.write(f"{subject}\t{area:.2f}\n")

def get_pial(files_in, path_in, path_out):
    surface_areas = {}
    cnt = 0

    for file_in in files_in:
        print('Processing pial, on {}%'.format(str(round(cnt/len(files_in)*100, 2))))
        _, subject = os.path.split(file_in)
        total_area = 0.0
        for hemi in ['lh', 'rh']:
            subject_path = os.path.join(path_in, file_in, 'surf', f'{hemi}.pial.T1')
            total_area += get_surface_area(subject_path)
        surface_areas[subject] = total_area
        cnt +=1
        
    output_file = os.path.join(path_out, 'total_pial_area.txt')    
    save_surface_areas_to_txt(surface_areas, output_file)
        
    return surface_areas
    

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
    get_pial(files, path_in, path_out)
    merge_all(path_out)


path_in = '/home/mireia/Desktop/01_PROJECTS/05_Isa/02_FS_7.4/RESULTS'
path_out = '/home/mireia/Desktop/01_PROJECTS/05_Isa/03_STRUCTURAL'
main(path_in, path_out)


# df1 = '/home/id05315/Desktop/03_Data/clemente/cov_for_combat.csv'
# df2 = '/home/id05315/Desktop/03_Data/clemente/final_output.csv'
# df1 = pd.read_csv(df1)
# df2 = pd.read_csv(df2)
# df1['Subject_ID'] = df1['Subject_ID'].apply(lambda x: '-'.join(x.split('-')[1:3]))
# df2['Subject_ID'] = df2['Subject_ID'].str.strip()
# merged = pd.merge(df1, df2, on='Subject_ID', how='inner')

# merged.to_csv('/home/id05315/Desktop/03_Data/clemente/final_output_2.csv', index=False)
