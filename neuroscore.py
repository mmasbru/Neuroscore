from feature_extractor import main_features 
from sklearn.impute import KNNImputer
import statsmodels.api as sm
import pandas as pd
import logging
import os

# Set up logging
def setup_logging(log_path):
    # Ensure the log directory exists, create it if not
    log_directory = os.path.dirname(log_path)
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    
    # Set up logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),  # Save log to the specified file path
            logging.StreamHandler()  # Also print logs to the console
        ]
    )

def check_columns(df, required_columns):
    """Check if the required columns exist in the dataframe."""
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing columns: {', '.join(missing_columns)}")

def make_unique_id_and_set_as_index(df, id_column='ID'):
    """Ensure that IDs are unique and set them as the index."""
    if id_column not in df.columns:
        raise ValueError(f"Column '{id_column}' not found in the dataframe.")
    
    try:
        df['unique_id'] = df.groupby(id_column).cumcount().astype(str)
        df[id_column] = df[id_column] + '_' + df['unique_id']
        df.set_index(id_column, inplace=True)
        df.drop(columns=['unique_id'], inplace=True)
    except Exception as e:
        logging.error(f"Error in make_unique_id_and_set_as_index: {e}")
        raise
    return df

def preprocess_data(df, covariates=['Age', 'Sex']):
    """Convert specified columns to numeric, coercing errors."""
    try:
        for col in covariates:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
            cols_all_zero = df.columns[(df == 0).all()]
            df = df.drop(columns=cols_all_zero)
            
    except KeyError as e:
        logging.error(f"Missing expected column for preprocessing: {e}")
        raise
    except Exception as e:
        logging.error(f"Error during preprocessing: {e}")
        raise
    return df

def regress_out_covariates(df, dependent_vars, covariates=['Age', 'Sex']):
    """Regress out the effects of covariates."""
    residuals_dict = {}
    for var in dependent_vars:
        if var not in covariates:
            try:
                df[var] = pd.to_numeric(df[var], errors='coerce')  # Ensure variable is numeric
                df_sub = df.dropna(subset=[var] + covariates)

                y = df_sub[var]
                X = df_sub[covariates]
                X = sm.add_constant(X)
                model = sm.OLS(y, X).fit()

                predicted = model.predict(X)
                residuals = y - predicted

                residuals_full = pd.Series(index=df.index, dtype='float64')
                residuals_full.loc[df_sub.index] = residuals
                residuals_dict[var] = residuals_full
            except KeyError as e:
                logging.error(f"Missing expected column for regression: {e}")
                raise
            except Exception as e:
                logging.error(f"Error in regression for {var}: {e}")
                raise
    return residuals_dict

def zscore_and_impute(df):
    """Z-score and impute missing values."""
    try:
        zscore_df = (df - df.mean()) / df.std(ddof=0)
        imputer = KNNImputer(n_neighbors=5)
        imputed_df = pd.DataFrame(imputer.fit_transform(zscore_df), columns=zscore_df.columns)
    except Exception as e:
        logging.error(f"Error in z-scoring and imputing: {e}")
        raise
    return imputed_df

def compute_neuroscore(zscore_residuals_imp, beta):
    """Compute the neuroscore."""
    try:
        common_columns = zscore_residuals_imp.columns.intersection(beta.columns)
        weighted_residuals = zscore_residuals_imp[common_columns] * beta[common_columns].values
        neuroscore = weighted_residuals.sum(axis=1)
    except KeyError as e:
        logging.error(f"Missing column during neuroscore computation: {e}")
        raise
    except Exception as e:
        logging.error(f"Error in neuroscore computation: {e}")
        raise
    return neuroscore

# Main execution
def main(path_fs, path_tab, wd_beta, log_path, path_demo):
    # Set up logging
    setup_logging(log_path)

    # Log the start of the execution
    logging.info("Execution started.")

    try:
        # Load data
        df = main_features(path_fs, path_tab, path_demo)
        df.index.name = 'ID'
        df = df.reset_index()
        # df = pd.read_csv(wd, delimiter=',')
        beta = pd.read_csv(wd_beta, index_col=0)

        # Check for required columns
        required_columns = ['ID','Sex', 'Age']
        check_columns(df, required_columns)

        # Handle redundant IDs and set index
        df = make_unique_id_and_set_as_index(df, id_column='ID')
        df = preprocess_data(df, ['Age', 'Sex'])
        beta = beta.apply(pd.to_numeric, errors='coerce').fillna(0)
        dependent_vars = [col for col in df.columns if col not in ['Age', 'Sex', 'ID']]
        residuals_dict = regress_out_covariates(df, dependent_vars)
        residuals_df = pd.concat(residuals_dict, axis=1)
        zscore_residuals_imp = zscore_and_impute(residuals_df)
        neuroscore = compute_neuroscore(zscore_residuals_imp, beta)
        neuroscore = pd.DataFrame(neuroscore, columns=['Neuroscore'])
        neuroscore.index = df.index
        neuroscore = pd.concat([df, neuroscore], axis = 1)

        # Log successful completion
        logging.info("Execution completed successfully.")

        # Output the result
        return neuroscore

    except Exception as e:
        # Log the error if something goes wrong
        logging.error(f"Error during execution: {e}")
        raise

# wd = '/home/mireia/Desktop/01_PROJECTS/05_Espectro/STRUCT/struct_demo.csv'  # Replace with your actual data path
# wd_beta = '/home/mireia/Desktop/01_PROJECTS/05_Espectro/betas.csv'  # Replace with your actual beta path
# log_path = '/home/mireia/Desktop/01_PROJECTS/05_Espectro/neuroscore.log'  # Replace with your actual log path
# neuroscore = main(wd, wd_beta, log_path)

# path_fs = '/home/mireia/Desktop/01_PROJECTS/05_Espectro/FS'
# path_tab = '/home/mireia/Desktop/01_PROJECTS/05_Espectro/STRUCT'
# wd_beta = '/home/mireia/Desktop/01_PROJECTS/05_Espectro/betas.csv'
# log_path = '/home/mireia/Desktop/01_PROJECTS/05_Espectro/neuroscore.log'
# path_demo = '/home/mireia/Desktop/01_PROJECTS/05_Espectro/demo.csv'
# neuroscore = main(path_fs, path_tab, wd_beta, log_path, path_demo)
