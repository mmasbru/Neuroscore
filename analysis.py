import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.patches as mpatches
from sklearn.decomposition import PCA
from scipy.stats import zscore
from neuroCombat import neuroCombat  # Ensure this is from pyneurocombat
from sklearn.impute import SimpleImputer

# Load the full dataset
df = pd.read_csv('/home/id05315/Desktop/03_Data/clemente/final_output.csv')

colnames = df.columns[6:]
imputer = SimpleImputer(strategy='mean')
data_imputed = pd.DataFrame(imputer.fit_transform(df[colnames]), columns=colnames)
data_zs = data_imputed.apply(zscore)
df = pd.concat([df.iloc[:, :6], data_zs], axis=1)

# Prepare the covariates DataFrame with the batch variable
covars = pd.DataFrame({
    'Site': df['Site'].values,     # this is your batch variable
    'Age': df['Age'].values,
    'Sex': df['Sex'].values,
    'Class': df['Class'].values
})

# Apply neuroCombat
combat_result = neuroCombat(
    dat=data_zs.T,            # (features x samples)
    covars=covars,            # must include batch + covariates
    batch_col='Site'          # name of the column in covars
)

# Retrieve the harmonized data and transpose back
data_combat = combat_result['data'].T  # Shape: (subjects, features)
combat_df = pd.DataFrame(data_combat, columns=colnames)
combat_df['Subject_ID'] = df['Subject_ID'].values
combat_df['Site'] = df['Site'].values
combat_df['Age'] = df['Age'].values
combat_df['Class'] = df['Class'].values
combat_df['Sex'] = df['Sex'].values
combat_df.to_csv('/home/id05315/Desktop/03_Data/clemente/combat_corrected_data.csv', index=False)


# Perform PCA with 5 components on the harmonized data
#data_combat = df[colnames].dropna().values
data_combat = df.iloc[:,6:]
pca = PCA(n_components=5)
pcs = pca.fit_transform(data_combat)
pca_df = pd.DataFrame(data=pcs, columns=['PC1', 'PC2', 'PC3', 'PC4', 'PC5'])

# Merge the PCA results with metadata columns 'Subject_ID' and 'Site'
merged_df = pd.concat([pca_df, df[['Subject_ID', 'Site', 'Class', 'Age', 'Sex', 'Etnia']].reset_index(drop=True)], axis=1)

# Define a color palette mapping for the 'Site' categories
unique_sites = merged_df['Site'].unique()
palette = sns.color_palette('tab10', n_colors=len(unique_sites))
site_palette = dict(zip(unique_sites, palette))

# Create a Seaborn pairplot with color coding by 'Site'
sns.set(style='whitegrid')
pairplot = sns.pairplot(
    merged_df,
    vars=['PC1', 'PC2', 'PC3', 'PC4', 'PC5'],
    hue='Site',
    palette=site_palette,
    diag_kind='kde',
    plot_kws={'alpha': 0.7, 's': 40}
)

# Remove the default legend if present
if pairplot._legend:
    pairplot._legend.remove()

# Create custom legend handles based on the site_palette
legend_handles = [mpatches.Patch(color=site_palette[site], label=site) for site in unique_sites]

# Add the custom legend to the figure
pairplot.fig.legend(handles=legend_handles, title="Site", loc='upper right', bbox_to_anchor=(0.95, 0.95))

# Adjust the layout and title
pairplot.fig.suptitle('Scatter Matrix of First 5 Principal Components (ComBat Corrected) Colored by Site', fontsize=16)
#pairplot.fig.suptitle('Scatter Matrix of First 5 Principal Components (Original) Colored by Site', fontsize=16)
pairplot.fig.tight_layout()
pairplot.fig.subplots_adjust(top=0.92)  # Ensure room for the title and legend

# Show the plot
plt.show()

# Save the plot
#pairplot.savefig('/home/id05315/Desktop/03_Data/clemente/pca_scatter_matrix.png')
pairplot.savefig('/home/id05315/Desktop/03_Data/clemente/pca_scatter_matrix_combat.png')
