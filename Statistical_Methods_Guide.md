# Statistical Methods Guide

**An explanation of every statistical method used in this project,
why it was chosen, and what it actually told us.**

This guide is for anyone reviewing the analysis who wants to understand the
reasoning behind the methods, not just the results. The document shows
how the analytical decisions were made.

---

## The big picture

This project asks two types of questions:

1. **What is associated with higher property values right now?** (cross-sectional)
2. **What changed between 2022 and 2024?** (longitudinal)

Different questions need different tools. Here is a summary of what was used
and why, followed by detailed explanations.

| Question | Method | Why this method |
|----------|--------|-----------------|
| Do properties with garages have higher assessed values? | Independent t-test | Comparing the means of two groups |
| Do different zoning categories have different values? | One-way ANOVA + Tukey HSD | Comparing means across 3+ groups |
| Do different parts of the city appreciate at different rates? | One-way ANOVA | Comparing means across 4 geographic quadrants |
| Does property age predict assessed value? | Simple linear regression | Testing if one numeric variable predicts another |
| Which features together explain assessed value? | Multiple linear regression (OLS) | Understanding the combined effect of several variables |
| Is the citywide appreciation significantly different from zero? | One-sample t-test | Testing whether an average is meaningfully different from a specific value |

---

## Method 1: Independent samples t-test

### Where it was used

Test 1: Comparing assessed values of properties with garages vs without garages.

### What it does in plain English

Imagine you have two piles of numbers: assessed values for homes with garages
and assessed values for homes without garages. The t-test asks: "Is the
difference between these two piles big enough that it probably did not happen
by chance?"

It calculates how far apart the two group averages are, relative to how spread
out the numbers are within each group. If the groups overlap a lot, the
difference might just be random noise. If they are clearly separated, the
difference is probably real.

### Why it was chosen

We had a simple setup: one binary variable (garage: yes or no) and one
numeric outcome (assessed value). The t-test is the standard tool for
exactly this situation. It is the simplest test that answers "are these
two groups different?"

We used Welch's t-test (the `equal_var=False` version) because the two
groups have different sizes (249K garage vs 111K no garage) and different
variances. Welch's version does not assume the groups have equal spread,
which makes it more reliable here.

### What it told us

The average assessed value for garage properties ($455K) is $287K higher
than non-garage properties ($169K). The p-value was essentially zero,
meaning this difference is not due to chance.

### Why the p-value alone is not enough

With 360,000 properties, even a $100 difference would be "statistically
significant." That is why we also reported:

- **95% confidence interval ($285K to $288K):** This tells us the true
  difference is almost certainly between these two values. The interval
  is tight because the sample is large.
- **Cohen's d (1.44):** This measures how big the difference is relative
  to the variability in the data. A d of 0.2 is small, 0.5 is medium,
  0.8 is large. Our d of 1.44 is very large, meaning the two groups are
  clearly separated.

### The catch

The $287K gap is not "the value of a garage." Properties with garages are
mostly detached houses. Properties without garages are mostly condos. The
t-test does not control for anything else. It just tells us the two groups
are different, not why. The regression in Section 5 addresses this by
controlling for other variables, which shrinks the gap to $116K.

---

## Method 2: One-way ANOVA with Tukey HSD post-hoc

### Where it was used

Test 2: Comparing assessed values across three zoning categories (Single
Family, Row/Townhouse, Apartment).

Test 3: Comparing appreciation rates across four geographic quadrants (NW,
NE, SW, SE).

### What it does in plain English

ANOVA is the t-test's bigger sibling. Instead of comparing two groups, it
compares three or more at the same time.

Think of it this way: if you had three classrooms of students and wanted to
know if their average test scores were different, you would not run three
separate t-tests (Class A vs B, A vs C, B vs C). That increases the chance
of a false positive. ANOVA runs one test that asks: "Is there any
significant difference among all these groups?"

If ANOVA says yes, it does not tell you which specific groups differ. That
is where Tukey HSD comes in. It runs all the pairwise comparisons (A vs B,
A vs C, B vs C) with a correction that accounts for the fact that you are
making multiple comparisons at once.

### Why it was chosen

For zoning (Test 2), we had three groups. For geographic quadrants (Test 3),
we had four groups. In both cases, we needed to compare means across more
than two categories. ANOVA is the standard approach.

We could have run multiple t-tests, but that inflates the risk of finding
a "significant" result by chance (the multiple comparisons problem). ANOVA
with Tukey HSD avoids this.

### What it told us

**Zoning (Test 2):** Single Family ($425K mean) is significantly higher
than Row/Townhouse ($165K) and Apartment ($118K). All three pairs are
significantly different from each other.

**Geographic quadrants (Test 3):** South Edmonton appreciated +6% while
North Edmonton was flat at -0.5%. The F-statistic of 12,809 is enormous,
meaning the geographic divide is not just visible in the charts but
confirmed by formal testing.

### Why Tukey HSD matters

Without Tukey, ANOVA only tells us "something is different." Tukey tells
us exactly which pairs differ. For the zoning test, Tukey confirmed that
every single pair (Single Family vs Row, Single Family vs Apartment,
Row vs Apartment) is significantly different, not just the extremes.

---

## Method 3: Simple linear regression

### Where it was used

Test 4: Testing whether property age predicts assessed value.

### What it does in plain English

Linear regression draws the best-fitting straight line through a scatter
plot. If you plot property age on the x-axis and assessed value on the
y-axis, regression finds the line that minimizes the total distance between
the dots and the line.

The **slope** tells you: for each additional year of age, how much does the
assessed value change on average?

The **R-squared** tells you: what percentage of the variation in assessed
value is explained by age alone? An R-squared of 1.0 means age perfectly
predicts value. An R-squared of 0.0 means age tells you nothing.

### Why it was chosen

We wanted to test whether older properties are worth less than newer ones.
Age is numeric and assessed value is numeric, so linear regression is the
natural tool. It gives us both a direction (positive or negative slope) and
a strength (R-squared).

### What it told us

The slope is -$1,759 per year: older properties are assessed slightly lower.
But R-squared is only 0.029, meaning age explains just 2.9% of the variance.
In other words, knowing a property's age tells you almost nothing about its
value. The scatter plot confirms this visually: at every age, properties
range from $50K to $2M+.

### Why this "weak" result is actually useful

A weak finding is still a finding. It tells us that property age is not a
meaningful standalone predictor, which challenges the common assumption that
"newer is always worth more." The reality is that a renovated 1970s home in
a good neighbourhood can be assessed higher than a brand-new condo. Location
and type matter far more than age.

---

## Method 4: Multiple linear regression (OLS)

### Where it was used

Section 5: Estimating the combined effect of lot size, property age, garage,
zoning, and location on assessed value.

### What it does in plain English

Simple regression uses one variable to predict an outcome. Multiple
regression uses several variables at the same time. This is important
because it lets each variable's effect be measured while holding the others
constant.

For example, the t-test showed a $287K garage premium. But is that really
about the garage, or is it because garage properties are bigger, newer, and
in better locations? Multiple regression answers this by saying: "If two
properties have the same lot size, same age, same zoning, and same location,
how much more is the one with a garage worth?"

### Why it was chosen

This is the core analytical tool for inference projects. We do not want to
just describe patterns (that is what EDA does). We want to estimate the
independent contribution of each feature to assessed value, controlling for
the others.

We used statsmodels OLS (Ordinary Least Squares) instead of scikit-learn
because statsmodels provides p-values, confidence intervals, and diagnostic
statistics for each coefficient. Scikit-learn's LinearRegression only gives
you coefficients and R-squared, which is not enough for inference.

### What it told us

- **Garage premium dropped from $287K to $116K** after controlling for lot
  size, zoning, age, and location. This is the single most important insight
  from the regression: more than half the raw gap was driven by confounding
  variables.
- **Latitude and longitude were the strongest features** by coefficient
  magnitude, confirming that location is the dominant factor.
- **Lot size adds $1.42 per square foot** of lot area.
- **Zoning Single Family was not significant (p = 0.357)** after controls.
  Once you account for lot size, garage, and location, the zoning label
  itself adds nothing. This makes sense: the label reflects what was built,
  and the building characteristics are already in the model.
- **R-squared was 15.9%.** This means the model explains about 16% of value
  differences using only external features. The other 84% comes from things
  we cannot see in the data: how big the house is inside, how many bedrooms
  it has, whether the kitchen was renovated last year.

### The diagnostics (and why they matter)

After running the regression, we checked three things:

1. **Residuals vs fitted plot:** The errors fan out as predicted values
   increase. This is called heteroscedasticity, and it means the model is
   less reliable for expensive properties than cheap ones. Common in
   property value models.

2. **Q-Q plot:** The residuals are not normally distributed (heavy right
   tail). This means the model systematically underpredicts high-value
   properties. A log transformation of assessed value would help, but we
   kept the model in raw dollars so coefficients are directly interpretable
   ("each year of age costs $2,284" is clearer than "each year of age
   reduces log-value by 0.006").

3. **Variance Inflation Factor (VIF):** This checks whether features are
   too correlated with each other (multicollinearity). Latitude and
   longitude had VIFs above 400,000 because they are inherently paired
   (they define a 2D point together). This is a known artifact and does not
   invalidate the model. The garage and Single Family zoning variables had
   VIFs of 16 and 28 respectively, reflecting their real-world correlation
   (most single family homes have garages). This explains why Single Family
   zoning was not significant: it is redundant once garage and lot size are
   in the model.

### Why we did not do train/test split

This is an inference model, not a prediction model. The goal is to
understand relationships, not to forecast the assessed value of a new
property. Train/test splits, cross-validation, and hyperparameter tuning
are tools for prediction. They are unnecessary here and would add
complexity without adding insight. If a hiring manager asks about this,
the answer is: "The project goal was inference, not prediction. I would
use train/test validation if building a predictive model."

---

## Method 5: One-sample t-test

### Where it was used

Section 6: Testing whether the citywide average appreciation is
significantly different from zero.

### What it does in plain English

The regular t-test compares two groups. The one-sample t-test compares one
group against a specific number. In our case: is the average appreciation
rate significantly different from 0%?

This might sound obvious ("of course it is, the average is +2.24%"). But
with high variance (standard deviation of 8.1%), it is possible that the
positive average is just noise. The t-test confirms whether we can trust
it.

### Why it was chosen

We needed to formally confirm that the citywide trend is real, not just
a visual impression from the charts. The one-sample t-test is the standard
tool for testing whether an average differs from a hypothesized value.

### What it told us

The t-statistic was 163.4 with p < 0.001. The +2.24% average appreciation
is real and statistically significant. However, the standard deviation of
8.1% means individual properties varied enormously around that average,
which is why the neighbourhood and zoning breakdowns are more informative
than the headline number.

---

## Method 6: Year-over-year property matching

### Where it was used

Section 6: Tracking how individual properties changed in value from 2022
to 2024.

### What it does in plain English

Each property in Edmonton has a unique account number. By joining the 2022
and 2024 datasets on this number, we can see how the same property's
assessed value changed over two years. This is more precise than comparing
citywide averages because it tracks the same physical property, not
different properties in different years.

### Why it was chosen

Comparing average values across years (e.g., "the average in 2022 was $X
and in 2024 it was $Y") is misleading because the mix of properties
changes. New homes are built, old ones are demolished, condos get converted.
Property-level matching eliminates this composition effect.

### What it told us

348,700 properties matched across both years (about 85% of the 2024
dataset). The 15% that did not match are mostly new construction built
after 2022. The matching allowed us to calculate per-property appreciation
rates and aggregate them by neighbourhood, zoning category, and geographic
quadrant, producing the project's strongest findings.

---

## Methods we did NOT use (and why)

| Method | Why it was not used |
|--------|---------------------|
| Chi-square test | Originally planned for testing value tiers by geography, but the bin boundaries would be arbitrary and any test would be "significant" at n = 360K. Replaced with the more natural ANOVA on appreciation by quadrant. |
| Logistic regression | No binary outcome to predict. Our target (assessed value) is continuous. |
| Random Forest / XGBoost | These are prediction tools. Our goal is inference (understanding relationships), not prediction (forecasting values). Tree-based models give better accuracy but worse interpretability. |
| Time series (ARIMA, Prophet) | Only 3 time points (2022, 2023, 2024). Time series models need dozens of observations to be meaningful. |
| Clustering (K-means) | Could be interesting for grouping neighbourhoods by appreciation pattern, but would add complexity without strengthening the core findings. A potential extension for future work. |
| Train/test split | Not applicable for inference. Explained above in the regression section. |

---

**Back to the main analysis:** [analysis.ipynb](../notebooks/analysis.ipynb)

**Back to the project overview:** [README.md](../README.md)