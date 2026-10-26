#### Data Exploration

240 rows x 7 columns

Columns:
**Temperature:** Surface temperature of the star in kelvin (integer). Ranges from 1,939 K to 40,000 K, with a mean of about 10,497 K and a standard deviation of about 9,552 K. The distribution is right-skewed (skewness ≈ 1.3): half the stars are cooler than roughly 3,300-ish K at the lower quartile, while a long tail of hot stars extends to 40,000 K.

**L:** Luminosity relative to the Sun, L/Lo (float), where Lo = 3.828 x 10^26 W. Ranges from 0.00008 to 849,420, a span of about 10 orders of magnitude. The mean (≈ 107,188) is far above the lower quartile (≈ 0.00087), and the distribution is strongly right-skewed (skewness ≈ 2.1). Raw values are unsuitable for plotting or distance-based models, so a log10 transform is needed.

**R:** Radius relative to the Sun, R/Ro (float), where Ro = 6.9551 x 10^8 m. Ranges from 0.0084 to 1,948.5. The lower quartile is about 0.10 and the upper quartile about 42.75, so most stars are small while a few giants are enormous (skewness ≈ 1.9). Also needs a log transform.

**A_M:** Absolute magnitude, Mv (float). Ranges from -11.92 (extremely bright) to 20.06 (extremely faint), with a mean of about 4.38. Unlike L and R, it is already on a logarithmic scale and is roughly symmetric (skewness ≈ -0.1), so it does not need transforming. Note that lower values mean brighter stars.

**Color:** General color of the star's spectrum (text). Contains 17 distinct strings, but they describe only about 8 real colors. Red is the most common label (112 rows) and blue is second (56). The inconsistencies are spelling and formatting only (for example "Blue-white", "Blue White", "Blue white" and "Blue-White", or "yellow-white" and "Yellowish White"), so this column needs standardizing before encoding.

**Spectral_Class:** Spectral classification of the star (text), with 7 values: M (111), B (46), O (40), A (19), F (17), K (6) and G (1). The classes are very imbalanced: M alone makes up about 46% of rows, while G has a single star. The letters follow a temperature sequence (O hottest to M coolest), so the column should be encoded as ordinal, not as unrelated categories.

**Type:** Target variable, an integer from 0 to 5 (0 Red Dwarf, 1 Brown Dwarf, 2 White Dwarf, 3 Main Sequence, 4 Super Giant, 5 Hyper Giant). Perfectly balanced, with exactly 40 stars per class.

##### State of the raw data

- **Missing values:** None in any column.
- **Duplicates:** No duplicate rows.
- **Data types:** Numeric columns were read correctly (Temperature and Type as integers, L, R and A_M as floats). Color and Spectral_Class are text.
- **Class balance:** The target is perfectly balanced (40 per class), so a majority-class baseline would score only 16.7% and accuracy is a fair metric.
- **Scale and skew:** Temperature, L and R are right-skewed and differ by many orders of magnitude, so they need log transformation and scaling. A_M is roughly symmetric.
- **Inconsistent labels:** Color has 17 spelling variants for about 8 real categories and must be cleaned.
- **Imbalanced categories:** Spectral_Class is dominated by M, with G represented by a single row, so rare categories may need merging or careful handling in cross-validation.
- **Relationship to the target:** Spectral_Class is strongly tied to Type. All Red Dwarfs and Brown Dwarfs are class M, while White Dwarfs appear only in A, B and F. However, M also contains 9 Super Giants and 22 Hyper Giants, so spectral class alone cannot identify a star's type.
- **Outliers:** Extreme values in L, R and Temperature are genuine features of giant and hot stars, not errors, so they should be kept and handled with transformations instead of being removed.
- **Overall:** The data is complete and compact (about 35 KB), but the dataset is small and needs cleaning of Color and scaling of the numeric columns before modeling.
