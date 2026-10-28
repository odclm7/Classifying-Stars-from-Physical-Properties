## Data Transformation

Notebook: `notebooks/03_data_transformation.ipynb` · Input: `data/stars_clean.csv` · Output: `data/stars_transformed.csv`

### Purpose

Re-express the cleaned data in a form suited to machine learning: reduce heavy skew in the numeric features and encode the categorical features as numbers. Unlike cleaning, this step changes the representation of values, not their correctness.

### 1. Skew correction

Temperature (skew 1.32), luminosity (2.07) and radius (1.95) are strongly right-skewed; luminosity spans about 10 orders of magnitude and radius about 5. Absolute magnitude (skew -0.12) is already symmetric and is left unchanged.

Eight transformations were compared on skewness, kurtosis, Shapiro-Wilk W, visual shape and cross-validated model accuracy (logistic regression, KNN, SVM, with a random forest as a control).

| Transformation | Mean abs. skew | CV accuracy* |
|---|---|---|
| Raw | 1.77 | 0.970 |
| Square root | 1.17 | 0.974 |
| Cube root | 0.96 | 0.978 |
| **Log10 (selected)** | **0.33** | **0.985** |
| Reciprocal | 1.65 | 0.880 |
| Box-Cox | 0.14 | 0.984 |
| Yeo-Johnson | 0.32 | 0.983 |
| Quantile (normal) | 0.01 | 0.939 |

\*Mean across the three scale-sensitive models.

**Decision: log10.** It brings every skewed column below 0.5 absolute skew (Temperature 0.44, L 0.19, R 0.36), gives the highest mean accuracy, is a fixed formula with no parameter learned from 240 samples (unlike Box-Cox and Yeo-Johnson), is easy to invert for the app, and matches the logarithmic axes astronomers use. Box-Cox reduces skew slightly further, but its accuracy is indistinguishable from log10, so simplicity and stability decided it. Full reasoning is in `docs/03_skew_transformation.md`.

### 2. Categorical encoding

- **Spectral_Class → ordinal (0 to 6).** The classes have a natural temperature order (O hottest to M coolest), so O=0, B=1, A=2, F=3, G=4, K=5, M=6 keeps that information.
- **Color → one-hot (7 columns).** The 7 colors have no meaningful order, so each becomes its own 0/1 column.

### 3. Final feature table

12 features plus the target:

| Group | Columns |
|---|---|
| Log-transformed numeric | `log_Temperature`, `log_L`, `log_R` |
| Unchanged numeric | `A_M` |
| Ordinal | `Spectral_Ordinal` |
| One-hot color | `color_blue`, `color_blue-white`, `color_orange`, `color_red`, `color_white`, `color_yellow`, `color_yellow-white` |
| Target | `Type`, `Type_Name` |

### What is deliberately not done here

**Feature scaling.** Standardization learns a mean and standard deviation, so it is applied inside the modeling pipeline and fitted on training folds only, to avoid leaking test information. Log transforms and the encodings above use fixed rules, so applying them to the full dataset before splitting does not leak.

### Notes and caveats

- Tree-based models do not need the log transform, but it benefits logistic regression, KNN and SVM and makes plots readable, so one transformed table is used for all models.
- Spectral_Class carries a data-quality warning from the cleaning step (24% of stars conflict with the expected temperature range), so the modeling stage should test its contribution with an ablation.
- Absolute magnitude is strongly related to luminosity (correlation about -0.98), so the final feature set contains redundant information. This is examined during modeling.

### Output

`data/stars_transformed.csv`: 240 rows, 12 feature columns plus `Type` and `Type_Name`.