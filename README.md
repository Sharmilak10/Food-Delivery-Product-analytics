# Food Delivery App — Product Analytics & A/B Testing

This project simulates user behavior inside a food delivery app and analyzes where users drop off in the ordering funnel.

The main goal was to identify friction points in the product experience and test whether a simplified checkout flow improves conversion.

The project covers the full workflow:
- synthetic data generation
- SQL funnel analysis
- A/B experiment design
- statistical significance testing
- business impact estimation
- data visualization

---

# Key Result

The largest drop in the funnel happened at the final checkout stage.

A simplified one-page checkout significantly improved checkout completion rates.

| Metric | Control | Treatment |
|---|---|---|
| Checkout conversion | 81.43% | 86.12% |
| Absolute lift | — | +4.69pp |
| P-value | — | 0.000001 |
| 95% Confidence Interval | — | [+2.80pp, +6.58pp] |
| Estimated monthly revenue impact | — | +₹24.6 lakh/month |

The result was statistically significant, and the analysis supports rolling out the new checkout flow to all users.

---

# Business Questions Explored

This project focuses on six core product analytics questions:

1. Where do users drop off in the funnel?
2. Which funnel step loses the most users?
3. Does the simplified checkout actually improve conversion?
4. Do Android and iOS users behave differently?
5. How do new users compare to returning users?
6. When are peak ordering hours?

---

# Project Structure

bash food_delivery_analytics/  ├── generate_data.py ├── ab_testing.py ├── visualization.py │ ├── data/ │   └── raw/ │ ├── sql/ │ ├── outputs/ │   ├── ab_test_results.png │   └── outputcharts/ │       ├── chart1_funnel.png │       ├── chart2_segment.png │       ├── chart3_user_type_segment.png │       └── chart4_peak_hours.png │ └── README.md 

---

# Funnel Analysis

The simulated funnel tracked 10,000 users across six product events.

text App Open          10,000  (100%) Restaurant Click   9,878  (98.8%) Menu View          9,596  (96.0%) Add to Cart        8,619  (86.2%) Checkout Started   7,742  (77.4%) Order Placed       6,354  (63.5%) 

The biggest drop occurred between:
- checkout started
- order placed

This suggested that users were interested enough to begin checkout but experienced friction before completing payment.

Funnel

---

# A/B Test — Simplified Checkout

The experiment compared:
- the original multi-step checkout
- a simplified one-page checkout

Users were randomly assigned to either:
- control
- treatment

The experiment ran from October–December 2024.

Primary metric:
- checkout-to-order conversion rate

## Experiment Results

text                 Converted    Not Converted    Total  Control            2,368              540    2,908 Treatment          2,525              407    2,932 

## Statistical Test

text Chi-square statistic : 23.27 P-value              : 0.000001 95% CI               : [+2.80pp, +6.58pp] 

The p-value indicates that the improvement is very unlikely to be caused by random chance.

The confidence interval also remains fully above zero, which supports the conclusion that the treatment genuinely improved conversion.

A/B Test

---

# Segment Analysis

## Android vs iOS

iOS users converted at a higher rate than Android users.

| Device | Conversion Rate |
|---|---|
| Android | 61.3% |
| iOS | 69.8% |

Possible explanations:
- payment flow issues
- performance differences
- UI inconsistencies across devices

Device Segment

---

## New vs Returning Users

Returning users converted much better than first-time users.

| User Type | Conversion Rate |
|---|---|
| Returning | 65.2% |
| New | 27.2% |

This suggests that onboarding and first-time checkout experience may need improvement.

Potential opportunities:
- fewer form fields
- first-order discounts
- better trust indicators
- saved address prompts

User Type

---

## Peak Ordering Hours

Order volume peaked during dinner hours, especially around 9pm.

The 6pm–10pm window drove the majority of orders.

This has operational implications for:
- delivery staffing
- notification timing
- infrastructure scaling

Peak Hours

---

# Recommendations

### 1. Roll out the simplified checkout
The experiment showed a clear and statistically significant improvement in conversion.

### 2. Investigate Android conversion gaps
The Android vs iOS difference is large enough to justify deeper investigation into payment failures and UI performance.

### 3. Improve first-time user onboarding
New user conversion rates indicate significant onboarding friction.

### 4. Prioritize dinner-hour reliability
Most revenue-generating activity occurs during the evening ordering window.

### 5. Experiment with menu optimization
A noticeable number of users browse menus without adding items to cart.

---

# How to Run

bash # Clone repository git clone https://github.com/YOUR_USERNAME/food-delivery-analytics.git  cd food-delivery-analytics  # Install dependencies pip install faker pandas numpy scipy matplotlib  # Generate synthetic data python generate_data.py  # Run analysis python ab_testing.py python visualization.py 

---

# Dataset Overview

| Metric | Value |
|---|---|
| Users | 10,000 |
| Sessions | 48,418 |
| Events | 160,557 |
| Date Range | Jan 2023 – Dec 2024 |
| Cities | 10 Indian cities |
| Device Split | Android 73.7% · iOS 26.3% |
| Dataset Type | Synthetic |

The dataset was generated using Python, Faker, NumPy, and seeded randomness for reproducibility.

---

# Tech Stack

- Python
- Pandas
- NumPy
- SciPy
- Matplotlib
- MySQL
- Faker
- Git

---

# Skills Demonstrated

- Funnel Analysis
- A/B Testing
- Statistical Significance Testing
- Confidence Intervals
- SQL Analytics
- Product Metrics
- Segment Analysis
- Business Impact Estimation
- Data Visualization

---


Sharmila Kummari

