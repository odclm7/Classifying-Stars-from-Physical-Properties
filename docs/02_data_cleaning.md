## Data Cleaning

Notebook: `notebooks/02_data_cleaning.ipynb` · Input: `data/Stars.csv` · Output: `data/stars_clean.csv`

### Purpose

Make the data correct and consistent without changing what the values mean. The raw file is never edited; all changes are made on a copy and are reproducible from the notebook.

### Steps and findings

| Step | What was done | Result |
|---|---|---|
| Structural checks | Checked shape, types, missing values, duplicates | 240 x 7, no missing values, no duplicates |
| Text formatting | Stripped whitespace, lowercased Color, replaced hyphens, uppercased Spectral_Class | Color labels reduced from 17 to 12 |
| Color merging | Merged spelling and near-synonym variants with an explicit mapping | 12 to 7 categories |
| Validity checks | Asserted positive Temperature, L, R; Type in 0 to 5; Spectral_Class in O, B, A, F, G, K, M | All passed |
| Readable target | Added `Type_Name` from the numeric code | 6 named classes |
| Consistency check | Compared Spectral_Class with conventional temperature ranges | 57 of 240 stars flagged |
| Outlier review | IQR rule on raw and log scales | No errors found; kept all rows |
| Physics check | Compared L with the Stefan-Boltzmann prediction | Large deviations; flagged, not corrected |

### Color standardization

Two kinds of merging
   1. Formatting merges (17 → 12): necessary and safe. “Blue White”, “Blue white”, “Blue-white” and “Blue-White” are the same label typed four ways. Lowercasing and replacing hyphens loses no information.

   2. Semantic merges (12 → 7): They assume that labels like “yellowish white” and “yellow white” mean the same thing.
   
   Further merging of near-synonyms (for example "yellow white" and "yellowish white") was deliberately **not** applied to the modeling column. The labels differ in how they relate to star type: all 8 "yellow white" stars are main sequence, while all 3 "yellowish white" stars are white dwarfs, so merging them would discard a possible signal. A coarser `Color_Group` column (7 groups) is provided for readable plots only. Three labels occur once (orange red, pale yellow orange, white yellow); rare labels are pooled inside the modeling pipeline using a frequency threshold learned from training data.

   Cross-validation showed color adds little when temperature, luminosity, radius and magnitude are available, and finer labels perform as well as or slightly better than merged ones when color is the main extra signal. Color granularity is therefore tested as an ablation during modeling.

   After formatting and merging, 'Color_Group' column has 7 categories remain: red (112), blue (56), blue-white (41), white (12), yellow-white (12), orange (4), yellow (3). Two merges are judgment calls ("pale yellow orange" and "orange red" both mapped to orange), so they are documented here and are easy to change in the mapping dictionary.

### Issues found but not "fixed"

- **Spectral class and temperature disagree for 57 of 240 stars (24%).** For example, 28 of the 40 class O stars have temperatures below 30,000 K, and one O star is at 5,752 K. Class O is conventionally the hottest class, so these labels are questionable. Because the conventional temperature boundaries are approximate, some mismatches (such as an M star at 3,834 K) are borderline, but the O, F and A groups show clear conflicts. The rows are kept and marked in a `spectral_temp_mismatch` column, since there is no reliable way to know which value is wrong. This is also a reason to treat Spectral_Class with caution as a model feature.
- **Luminosity is inconsistent with radius and temperature.** For a blackbody, L = R^2 (T / 5772)^4 in solar units. In this data the log10 ratio of recorded to expected luminosity has a mean of -0.29, a standard deviation of 1.15 and a maximum deviation of 4.3 orders of magnitude, so the dataset is not physically self-consistent. It is documented as a limitation, and no values were altered.
- **Outliers are not errors.** The IQR rule flags 11 Temperature, 12 luminosity and 40 radius values on the raw scale, but none on the log scale (and none for A_M). They are the legitimate giants and hot stars in a skewed distribution, so all rows are kept and the skew is handled in the transformation step.

### Decisions summary

- No rows dropped, no numeric values changed.
- Text categories standardized; target given readable names.
- Two data-quality concerns (spectral/temperature mismatch, physics inconsistency) recorded and carried forward as limitations.

### Output

`data/stars_clean.csv`: 240 rows, original columns plus `Type_Name` and `spectral_temp_mismatch`.