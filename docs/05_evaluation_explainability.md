## Evaluation, Explainability and External Validation
 
Notebook: `notebooks/05_evaluation_explainability.ipynb`
Inputs: `data/stars_clean.csv`, `models/star_classifier.joblib` · Outputs: `models/model_metadata.json`, figures in `reports/figures/`
 
### Purpose
 
The model-comparison stage selected a random forest on four features (log T, log L, log R, absolute magnitude). Cross-validated accuracy was already about 100%, so another accuracy figure adds little. This stage asks the questions that remain:
 
1. Does the model hold up on the held-out test set?
2. Are its probabilities trustworthy, since the app displays them?
3. What is the model actually relying on?
4. Does it work on **real stars**, not just the 240 in this dataset?
### 1. Held-out test evaluation
 
The 48-star test set (8 per class) was not used for comparison or tuning, and was evaluated once.
 
| Metric | Result |
|---|---|
| Accuracy | 1.000 |
| Macro F1 | 1.000 |
| Log loss | 0.015 |
| Misclassified stars | 0 of 48 |
 
Precision, recall and F1 are 1.000 for every one of the six classes. With 48 stars, a single error would have cost 2.1 percentage points, so this result is consistent with, and no stronger than, the cross-validation results from the comparison stage. The confusion matrix is purely diagonal (`reports/figures/confusion_matrix_test.png`).
 
### 2. Error analysis on out-of-fold predictions
 
To use more data than 48 stars, every training star was predicted by a model that had not seen it (5-fold out-of-fold predictions).
 
- Out-of-fold accuracy: **1.000**; misclassified stars: **0 of 192**.
With no errors to study, the analysis focuses on **confidence**: which stars is the model least sure about?
 
| Class | Mean confidence | Lowest confidence |
|---|---|---|
| White dwarf | 0.994 | 0.880 |
| Hyper giant | 0.990 | 0.910 |
| Super giant | 0.984 | 0.830 |
| Red dwarf | 0.976 | 0.750 |
| Main sequence | 0.966 | 0.557 |
| Brown dwarf | 0.966 | 0.767 |
 
The model is most certain about white dwarfs and hyper giants, which sit in extreme corners of the radius and magnitude space, and least certain about main sequence and brown dwarf stars.
 
The least confident star overall (confidence 0.557) is a main sequence star with temperature 36,108 K, luminosity 198,000 and radius 10.2: it is very hot and bright, which resembles the super giant region, even though its small radius places it on the main sequence. The next lowest are a main sequence star at 4,077 K (0.647), then red and brown dwarfs between 0.75 and 0.82, which are the neighbouring faint classes. Low confidence therefore marks stars near a class boundary, which is useful behaviour for the app.
 
### 3. Calibration
 
Calibration asks whether a stated confidence matches reality: of the stars predicted at about 90%, are about 90% correct?
 
| Confidence bin | Stars | Mean confidence | Accuracy |
|---|---|---|---|
| 0.5 to 0.7 | 2 | 0.602 | 1.000 |
| 0.7 to 0.9 | 11 | 0.840 | 1.000 |
| 0.9 to 1.0 | 179 | 0.992 | 1.000 |
 
Expected calibration error (ECE): **0.021**.
 
Interpretation:
 
- The model is **underconfident**, not overconfident: in every bin the real accuracy (100%) is at or above the stated confidence. This is typical of random forests, which average many trees and therefore rarely output extreme probabilities for borderline stars.
- Underconfidence is the safer failure direction for an app: a displayed "60%" is conservative.
- Only 13 stars fall below 0.9 confidence and none are wrong, so this check cannot reveal overconfidence in rare errors. The real-star check below tests that more directly.
### 4. Feature importance
 
| Feature | Impurity importance | Permutation: log-loss increase (± std) | Permutation: accuracy drop |
|---|---|---|---|
| log R | 0.400 | 0.629 ± 0.053 | 0.279 |
| A_M | 0.380 | 0.741 ± 0.068 | 0.188 |
| log L | 0.136 | 0.272 ± 0.032 | 0.011 |
| log T | 0.083 | 0.113 ± 0.021 | 0.000 |
 
Permutation importance shuffles one feature on the test set and measures how much the model degrades. It was scored on log loss because accuracy is saturated and shows almost no change for the weaker features.
 
Interpretation:
 
- **Radius and absolute magnitude dominate** under both measures, which agrees with the ablation study (adding radius gained about 15 points, adding magnitude about 3 to 5).
- **Temperature barely matters to the model**: shuffling it costs no accuracy at all. It still raises log loss slightly, so it contributes a little confidence, but the classes are almost entirely separable by size and brightness.
- **Caution with correlated features.** Luminosity and absolute magnitude are almost perfectly correlated (about -0.98). When one is shuffled, the other still carries the same information, so permutation importance understates both. The small accuracy drop for log L (0.011) is partly a result of this redundancy and should not be read as "luminosity is unimportant".
### 5. Human-readable rules
 
A depth-4 decision tree (not the deployed model) summarises the class boundaries. Its 5-fold cross-validated accuracy is 0.890 ± 0.089.
 
```
log R <= -1.48                      (R < 0.033)   -> White Dwarf
log R >  -1.48
  log R <= -0.14                    (R < 0.72)
     A_M <= 15.49                                 -> Brown Dwarf
     A_M >  15.49                                 -> Red Dwarf
  log R >  -0.14
     A_M <= -7.51                                 -> Hyper Giant
     A_M >  -7.51
        log R <= 1.04               (R < 11)      -> Main Sequence
        log R >  1.04                             -> Super Giant
```
 
Reading it as astrophysics: white dwarfs are identified by being tiny; the two dwarf classes are then separated by brightness; very bright large stars are hyper giants; the remaining large stars split into main sequence and super giants by radius. **Temperature is never used.** This explains the importance results above.
 
The tree reaches only 89% because depth 4 is too shallow; the depth-5 tree in the comparison stage reached 99.8%. The rules are therefore a good summary of the main structure, not a complete description.
 
### 6. External validation on real stars
 
The dataset has only 240 rows and its luminosities are not physically self-consistent (see the cleaning notes), so strong performance on it may not carry over to real stars. As an independent check, the model classified 11 well-known stars using approximate catalogue values.
 
> **Verify before publishing.** The input values are approximate literature figures. Absolute magnitude mixes visual and bolometric conventions. Check each value against SIMBAD or another reference and cite the source in the notebook. The expected type is the commonly accepted classification mapped to this dataset's six classes.
 
| Star | Expected | Predicted | Confidence | Result |
|---|---|---|---|---|
| Sun | Main Sequence | Main Sequence | 1.000 | Correct |
| Vega | Main Sequence | Main Sequence | 1.000 | Correct |
| Sirius A | Main Sequence | Main Sequence | 1.000 | Correct |
| Proxima Centauri | Red Dwarf | Red Dwarf | 0.910 | Correct |
| Barnard's Star | Red Dwarf | Brown Dwarf | 1.000 | **Wrong** |
| Sirius B | White Dwarf | White Dwarf | 0.957 | Correct |
| Procyon B | White Dwarf | White Dwarf | 1.000 | Correct |
| Rigel | Super Giant | Super Giant | 0.530 | Correct |
| Antares | Super Giant | Hyper Giant | 0.533 | **Wrong** |
| Betelgeuse | Super Giant | Hyper Giant | 0.533 | **Wrong** |
| VY Canis Majoris | Hyper Giant | Hyper Giant | 1.000 | Correct |
 
**8 of 11 correct.** All inputs lie within the per-feature range of the training data, though that does not guarantee the combination of features is covered. Shifting every absolute magnitude by up to ±1 magnitude changed the result by at most one star (7 to 8 correct), so the result is not fragile to the magnitude convention.
 
What the three misses show:
 
- **Barnard's Star (red dwarf, predicted brown dwarf, 100% confident).** The tree rules draw the red/brown dwarf boundary at A_M of about 15.5, but real red dwarfs such as Barnard's Star (about 13.2) lie on the other side. In this dataset the "brown dwarf" class has a median magnitude of 12.6 and the "red dwarf" class 17.1, so its labels do not match the standard astronomical meaning. The model learned the dataset's convention faithfully; the convention is the problem. This is also the most worrying miss, because it was made with full confidence.
- **Antares and Betelgeuse (red supergiants, predicted hyper giant, about 53%).** In this dataset hyper giants are cool (median 3,766 K) and super giants are hot (median 12,821 K), so the model learned "cool, huge and bright means hyper giant". Real red supergiants fit that pattern. Their low confidence (53%) shows the model is appropriately unsure. Rigel, a correct prediction, also sits at 53%, so this class boundary is the model's weakest region.
These are findings about the **training data's labelling conventions**, not random model errors. They are the main reason to present the model as a demonstration and not as a classifier for real astronomy.
 
### 7. Implications for the app
 
- Display the predicted class together with its probabilities, since confidence is informative and conservative.
- Warn the user when the top probability is below 70% and name the runner-up class.
- Warn when any input falls outside the training range, because tree models cannot extrapolate.
- State the limitations in the interface, including the 8-of-11 real-star result.
### 8. Artifacts produced
 
| File | Purpose |
|---|---|
| `models/model_metadata.json` | Feature names, class names and training ranges used by the app |
| `reports/figures/confusion_matrix_test.png` | Test-set confusion matrix |
| `reports/figures/calibration.png` | Confidence histogram and reliability plot |
| `reports/figures/feature_importance.png` | Impurity and permutation importance |
 
### 9. Limitations
 
- **Saturated results.** With no errors on the test set or in out-of-fold predictions, error analysis is limited to confidence.
- **Small samples.** 48 test stars and 11 real stars give wide uncertainty; the real-star result is illustrative, not statistically precise.
- **Approximate real-star values** and a mix of magnitude conventions.
- **Label conventions.** The dataset's class definitions differ from standard classification in at least two places (red/brown dwarfs, cool supergiants).
- **Redundant features** make permutation importance understate luminosity and magnitude.
### 10. Reproducing
 
Run order: notebooks 01 to 04, then this one. Notebook 04 ends with a cell that trains the final random forest and saves it to `models/star_classifier.joblib`; this notebook loads that file and fails with `FileNotFoundError` if the cell has not been run. The notebook recreates the same stratified split (`test_size=0.2`, `random_state=42`) on `data/stars_clean.csv`, so the test stars are the same ones held out during model selection. Do not re-sort or filter the cleaned data between notebooks. All random seeds are fixed.