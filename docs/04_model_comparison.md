## Model Comparison and Selection
 
Notebook: `notebooks/04_model_comparison.ipynb` (comparison, tuning and selection in one notebook)
Input: `data/stars_transformed.csv` · Output: `models/star_classifier.joblib`
 
### Purpose
 
Decide which model and which input features to deploy in the web app. The dataset is small (240 stars) and several models reach near-perfect accuracy, so the comparison is designed to answer more than "which model scores highest":
 
1. Which **features** are worth collecting from app users?
2. Which **models** are genuinely better, and which are only tied within noise?
3. Does **tuning** change the answer?
4. Which model is the best choice **for the application** (calibrated probabilities, robustness, explainability)?
### 1. Setup
 
**Train/test split.** 80/20, stratified on `Type`, `random_state=42`: 192 training stars and 48 test stars (8 per class in the test set). The test set is not used in model comparison or tuning. It is evaluated once, at the end.
 
**Why this matters for reading the results.** Each cross-validation fold tests on about 38 stars, so one misclassified star changes that fold's accuracy by about 2.6 percentage points (pp). Differences of 1 to 2 pp therefore amount to one or two stars and should not be treated as real.
 
### 2. Experimental design
 
#### 2.1 Feature sets
 
Feature sets are built up one step at a time, so the effect of each added feature can be measured by comparing neighbouring sets.
 
| Set | Features | Rationale |
|---|---|---|
| A | log T, log L | The two axes of the Hertzsprung-Russell diagram |
| B | A + log R | Adds stellar size |
| C | B + absolute magnitude (A_M) | Adds brightness on the magnitude scale; the numeric-only set |
| D | C + spectral class (ordinal) | Tests the label flagged in cleaning for temperature mismatches |
| E | D + color (one-hot, 12 labels) | Tests the free-text label column |
 
#### 2.2 Models
 
All use `random_state=42` where applicable. Logistic regression, KNN and SVM are wrapped in a pipeline with `StandardScaler`, so scaling is fitted on training folds only.
 
| Model | Configuration |
|---|---|
| Baseline | Always predicts the most frequent class |
| Logistic regression | `max_iter=5000`, default regularization |
| KNN | k = 5 |
| SVM | RBF kernel, `probability=True` |
| Decision tree | `max_depth=5` |
| Random forest | 300 trees |
| Gradient boosting | scikit-learn defaults |
 
#### 2.3 Evaluation protocol
 
5-fold stratified cross-validation repeated 5 times (25 folds per model and feature set; 7 models x 5 feature sets = 35 combinations, 875 fits in total), on the training set only.
 
| Metric | What it measures | Direction |
|---|---|---|
| Accuracy | Share of stars classified correctly | Higher is better |
| Macro F1 | F1 averaged equally over the 6 classes; penalizes uneven performance across classes | Higher is better |
| Log loss | How much probability the model gave to the true class; heavily penalizes confident wrong answers | **Lower** is better |
 
Log loss is included because the app displays class probabilities. Two models with identical accuracy can differ greatly in how trustworthy those probabilities are.
 
### 3. Results: accuracy by model and feature set
 
Mean cross-validated accuracy:
 
| Model | A: log T + log L | B: + log R | C: + A_M | D: + spectral | E: + color |
|---|---|---|---|---|---|
| Baseline (majority) | 0.156 | 0.156 | 0.156 | 0.156 | 0.156 |
| Decision tree | 0.830 | 0.943 | 0.998 | 0.989 | 0.997 |
| Gradient boosting | 0.789 | 0.952 | 0.989 | 0.985 | 0.984 |
| KNN (k = 5) | 0.787 | 0.950 | 0.987 | 0.976 | 0.921 |
| Logistic regression | 0.792 | 0.940 | 0.970 | 0.962 | 0.961 |
| Random forest | 0.806 | 0.959 | **1.000** | **1.000** | 0.998 |
| SVM (RBF) | 0.791 | 0.954 | 0.982 | 0.971 | 0.907 |
 
**How to read it.** The baseline of 0.156 is the floor, slightly below 1/6 because stratified folds of 192 stars are not exactly balanced. Every real model is far above it. Reading left to right shows how accuracy changes as features are added.
 
#### 3.1 Effect of each added feature
 
Change in accuracy (percentage points) when moving from one feature set to the next, computed with
`(acc.diff(axis=1).iloc[:, 1:] * 100).round(1)`:
 
| Model | A to B (adds log R) | B to C (adds A_M) | C to D (adds spectral) | D to E (adds color) |
|---|---|---|---|---|
| Decision tree | +11.3 | +5.5 | -0.9 | +0.8 |
| Gradient boosting | +16.3 | +3.7 | -0.4 | -0.1 |
| KNN | +16.3 | +3.7 | -1.1 | **-5.5** |
| Logistic regression | +14.8 | +3.0 | -0.8 | -0.1 |
| Random forest | +15.3 | +4.1 | 0.0 | -0.2 |
| SVM | +16.3 | +2.8 | -1.1 | **-6.4** |
 
Interpretation, using the fold-to-fold standard deviation (0.015 to 0.025 for most models) as the yardstick for what counts as real:
 
- **log R (A to B): a large, consistent gain of 11 to 16 pp for every model.** Temperature and luminosity alone leave several classes overlapping; radius separates them. It is the most valuable single addition.
- **A_M (B to C): a smaller but consistent gain of 3 to 5.5 pp.** Absolute magnitude is strongly related to luminosity (correlation about -0.98), yet it still helps, so it carries information not fully captured by `log_L` in this dataset.
- **Spectral class (C to D): no meaningful change.** All movements are between -1.1 and 0.0 pp, which is about one test star and below the noise level. Spectral class adds nothing, and it carries the temperature-mismatch problem identified in cleaning (24% of stars), so it is excluded.
- **Color (D to E): a real harm for KNN (-5.5 pp) and SVM (-6.4 pp); no effect on the others.** KNN and the RBF SVM work from distances between stars. After scaling, all columns count equally, so roughly a dozen mostly-zero one-hot color columns next to 4 informative numeric columns dominate the distance calculation. Tree models and logistic regression can ignore an unhelpful column, so they are unaffected.
#### 3.2 Top 15 results by accuracy, then log loss
 
| Rank | Feature set | Model | Accuracy | Std | Macro F1 | Log loss |
|---|---|---|---|---|---|---|
| 1 | C | Random forest | 1.000 | 0.000 | 1.000 | 0.022 |
| 2 | D | Random forest | 1.000 | 0.000 | 1.000 | 0.035 |
| 3 | E | Random forest | 0.998 | 0.007 | 0.998 | 0.063 |
| 4 | C | Decision tree | 0.998 | 0.007 | 0.998 | 0.076 |
| 5 | E | Decision tree | 0.997 | 0.009 | 0.997 | 0.114 |
| 6 | C | Gradient boosting | 0.989 | 0.015 | 0.988 | 0.024 |
| 7 | D | Decision tree | 0.989 | 0.013 | 0.988 | 0.414 |
| 8 | C | KNN | 0.987 | 0.020 | 0.987 | 0.072 |
| 9 | D | Gradient boosting | 0.985 | 0.015 | 0.985 | 0.026 |
| 10 | E | Gradient boosting | 0.984 | 0.017 | 0.984 | 0.026 |
| 11 | C | SVM | 0.982 | 0.019 | 0.982 | 0.150 |
| 12 | D | KNN | 0.976 | 0.020 | 0.975 | 0.087 |
| 13 | D | SVM | 0.971 | 0.021 | 0.970 | 0.157 |
| 14 | C | Logistic regression | 0.970 | 0.023 | 0.969 | 0.360 |
| 15 | D | Logistic regression | 0.962 | 0.024 | 0.962 | 0.331 |
 
What this table shows:
 
- **Accuracy is saturated.** The random forest on set C classified every star correctly in all 25 folds (std 0.000). With the ceiling reached, accuracy cannot rank the top models, so other criteria are needed.
- **Models are statistically tied on accuracy.** Random forest, decision tree, gradient boosting, KNN and SVM on set C lie within 0.982 to 1.000, and their standard deviations (0.007 to 0.020) are as large as the gaps. Only logistic regression is clearly behind.
- **Macro F1 closely follows accuracy** for every row, so no class is being sacrificed for overall accuracy (the dataset is perfectly balanced, so this is expected).
- **Log loss separates the models.** Random forest (0.022) and gradient boosting (0.024) give well-calibrated probabilities. The decision tree is much worse (0.076, and 0.414 on set D) despite near-equal accuracy: a single tree outputs probabilities of exactly 0 or 1 for each leaf, so its few mistakes are made with full confidence. Logistic regression is worst (0.360) because its linear boundary cannot represent the curved class regions.
- **Only tree models appear with set E** in the top 15, consistent with section 3.1.
### 4. Hyperparameter tuning
 
Because accuracy is saturated, tuning optimizes **log loss**, which still varies between configurations and directly affects the quality of the displayed probabilities. Nested cross-validation (inner 5-fold grid search, outer 5-fold evaluation) was used so that the tuned scores are not optimistic.
 
| Model | Grid searched |
|---|---|
| Random forest | n_estimators {200, 400}, max_depth {None, 6}, min_samples_leaf {1, 3} |
| Gradient boosting | n_estimators {100, 200}, learning_rate {0.05, 0.1}, max_depth {2, 3} |
| SVM | C {1, 10, 100}, gamma {scale, 0.1, 0.3} |
 
| Model | Default accuracy | Default log loss | Tuned accuracy | Tuned log loss | Best parameters |
|---|---|---|---|---|---|
| Random forest | 1.000 | 0.022 | 1.000 (std 0.000) | 0.023 | max_depth None, min_samples_leaf 1, n_estimators 200 |
| Gradient boosting | 0.989 | 0.024 | 0.995 (std 0.010) | **0.006** | learning_rate 0.1, max_depth 2, n_estimators 100 |
| SVM | 0.982 | 0.150 | 0.989 (std 0.013) | 0.153 | C 10, gamma scale |
 
*Note: tuned values come from a verification run with 5 outer folds and 1 repeat; if you ran more repeats, replace them with your notebook's output. They are less precise than the 5x5 default results and are not directly comparable to them.*
 
Interpretation:
 
- **Random forest: tuning changed nothing.** The best configuration is essentially the default, so the default model is kept. This is a useful negative result: further tuning is unnecessary.
- **Gradient boosting improved substantially in log loss** (0.024 to 0.006) with shallow trees (depth 2), which suggests the default depth was too complex for 192 samples. A log loss this low on a small training set can also mean overconfidence, so it needs the robustness check below before being trusted.
- **SVM: no meaningful change.**
### 5. Robustness to input noise
 
Real users will enter approximate values. To test sensitivity, Gaussian noise was added to the held-out folds (training data left clean) at two levels: mild (0.05 in log10 units, about 12%, and 0.3 magnitudes) and heavy (0.15 log10 units, about 40%, and 1.0 magnitude). Accuracy on set C:
 
| Model | Mild noise | Heavy noise |
|---|---|---|
| Random forest | 0.991 | 0.950 |
| SVM | 0.981 | 0.962 |
| Decision tree | 0.988 | 0.926 |
| Logistic regression | 0.967 | 0.924 |
| Gradient boosting (default) | 0.963 | 0.879 |
 
*KNN and the tuned gradient boosting model were not included in this test.*
 
Random forest is the most accurate under mild noise and SVM is slightly better under heavy noise. Default gradient boosting degrades the most, so its high accuracy on clean data does not translate into stability. The tuned boosting model should be stress-tested before it is considered as an alternative.
 
### 6. Model selection
 
#### 6.1 Selection criteria (in priority order)
 
1. **Inputs users can provide.** The feature set must be practical to collect in the app.
2. **Predictive performance** within statistical noise of the best.
3. **Calibrated probabilities** (log loss), since the app displays them.
4. **Robustness** to noisy inputs.
5. **Simplicity and explainability.**
Because the top models are tied on accuracy, criteria 3 to 5 decide.
 
#### 6.2 Decision
 
| Item | Decision | Reasoning |
|---|---|---|
| Feature set | **C: log T, log L, log R, A_M** | Best or tied-best for nearly every model; spectral class adds nothing and color harms some models; only four numeric inputs are required from the user |
| Deployed model | **Random forest** | Perfect cross-validated accuracy and F1, lowest default log loss (0.022), most accurate under mild noise, no tuning needed, no scaling required, explainable via feature importance and SHAP |
| Challenger | Gradient boosting (tuned) | Nearly as accurate with excellent log loss, but unproven for robustness |
| Reference model | SVM | A smooth-boundary model, most stable under heavy noise; useful for comparing behaviour on real stars |
| Rejected | Logistic regression | Poorly calibrated (log loss 0.36) and lowest accuracy among serious candidates |
| Rejected | KNN | Degraded sharply by extra features; sensitive to scaling |
| Explanation only | Decision tree (depth 5) | Near-perfect accuracy with human-readable rules, but unstable and overconfident as a deployed model |
 
#### 6.3 Final model
 
The deployed pipeline accepts raw values and applies the log transform internally, so the app needs no separate preprocessing code:
 
```python
final = make_pipeline(
    ColumnTransformer(
        [("log", FunctionTransformer(np.log10), ["Temperature", "L", "R"])],
        remainder="passthrough"),
    RandomForestClassifier(n_estimators=300, random_state=42),
)
final.fit(Xr_train[["Temperature", "L", "R", "A_M"]], yr_train)
joblib.dump(final, "../models/star_classifier.joblib")
```
 
The log step is not required for a random forest but is kept so the pipeline is interchangeable with the SVM or boosting alternatives and consistent with the rest of the project.
 
### 7. Held-out test evaluation
 
The test set (48 stars) was used once, after selection was complete.
 
| Metric | Result |
|---|---|
| Accuracy | [fill in from notebook] |
| Macro F1 | [fill in from notebook] |
| Misclassified stars | [fill in from notebook] |
 
*Replace the placeholders with the output of the final evaluation cell. With only 48 test stars, one error is 2.1 pp, so report the cross-validation results alongside this figure.*
 
### 8. Limitations
 
- **Saturated accuracy.** The ceiling is reached on this dataset, so the data cannot distinguish the strongest models by accuracy. The conclusions rely on log loss and robustness, which are secondary evidence.
- **Small sample.** 192 training stars give wide uncertainty; differences under about 2 pp are within one or two stars.
- **Physically inconsistent source data.** Cleaning showed that recorded luminosity does not follow the Stefan-Boltzmann relation, so performance on this dataset may not carry over to real stars.
- **Tree models do not extrapolate.** A star outside the training range will be assigned the class of the nearest region, with no warning. The app should warn when inputs fall outside the training range.
- **Tuning results** are from a single repeat of nested cross-validation and are indicative, not definitive.
- **Not yet externally validated.** Testing against catalogued real stars is the next step (notebook 06).
### 9. Reproducing the tables
 
| Table | Notebook step |
|---|---|
| Accuracy by model and feature set | `results.pivot(index="model", columns="feature set", values="accuracy")` |
| Effect of each added feature | `(acc.diff(axis=1).iloc[:, 1:] * 100).round(1)` |
| Top 15 ranking | `results.sort_values(["accuracy", "log_loss"], ascending=[False, True]).head(15)` |
| Tuned results | Nested cross-validation cell (log-loss scoring) |
| Noise robustness | `stress_cv` cell |
 
All random seeds are fixed (`random_state=42` for the split, models and cross-validation), so the results are reproducible.