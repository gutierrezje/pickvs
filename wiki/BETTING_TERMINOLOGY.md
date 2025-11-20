# Betting Terminology Guide

This document explains the uncommon betting terminology used throughout the PickVs system.

---

## Core Betting Concepts

### Pick
A **pick** is a single prediction made by a user on a specific outcome of an NBA game. Each pick:
- Is associated with one game and one betting market (moneyline, spread, or total)
- Has a standard stake of **1 unit**
- Is recorded with the odds available at the time of the pick
- Remains pending until the game finishes and can be graded

**Example**: "I pick Lakers to win (moneyline) at 1.91 odds"

---

## Betting Markets

### Moneyline
A **moneyline** bet is the simplest form of betting—you predict which team will win the game.

- **Outcome**: Win or Loss (no pushes)
- **Odds Format**: Decimal (e.g., 1.91, 2.10)
  - Home team odds example: 1.91 (meaning $1 profit on $1 wagered)
  - Away team odds example: 1.91 (symmetric for balanced games)
- **Result Calculation**:
  - **Win**: `result_units = (odds_at_pick - 1.0) * stake_units`
    - Example: 1.91 odds on 1 unit = 0.91 units profit
  - **Loss**: `result_units = -1.0 * stake_units` = -1.0 units

**Example Pick**: Lakers vs Warriors, pick Lakers to win at 1.91

---

### Spread
A **spread** bet is a handicap bet where the sportsbook assigns a point differential to level the playing field.

- **Spread Value**: Points given/taken (e.g., -6.5 for the favorite, +6.5 for the underdog)
  - **Negative spread** (-6.5): Favorite must win by MORE than 6.5 points
  - **Positive spread** (+6.5): Underdog can lose by up to 6.5 points OR win outright
- **Outcome**: Win, Loss, or **Push** (push = tie = no profit/loss)
- **Push Scenario**: If final score difference exactly equals the spread
  - Example: Lakers -6.5, actual difference = 6.5 exactly → Push → result_units = 0.0
- **Odds Format**: Decimal (typically 1.91, representing -110 American odds)
- **Result Calculation**:
  - **Win**: `result_units = (odds_at_pick - 1.0) * stake_units`
  - **Loss**: `result_units = -1.0 * stake_units`
  - **Push**: `result_units = 0.0`

**Example Pick**: Lakers vs Warriors, Lakers -6.5, pick Lakers at 1.91

---

### Total (Over/Under)
A **total** bet (also called Over/Under) predicts whether the combined score of both teams will be above or below a set number.

- **Spread Value**: The total points line (e.g., 220.5)
  - **Over**: Combined score > 220.5 (combined total goes over the line)
  - **Under**: Combined score < 220.5 (combined total goes under the line)
- **Outcome**: Win, Loss, or **Push** (if combined score equals exactly 220.5)
- **Odds Format**: Decimal (typically 1.91 for balanced totals)
- **Result Calculation**:
  - **Win**: `result_units = (odds_at_pick - 1.0) * stake_units`
  - **Loss**: `result_units = -1.0 * stake_units`
  - **Push**: `result_units = 0.0`

**Example Pick**: Lakers vs Warriors, Over 220.5, pick Over at 1.91

---

## Odds & Pricing

### Decimal Odds
Decimal odds (also called European odds) represent the total return for a 1 unit stake, including the original stake.

- **Format**: Number with 2 decimal places (e.g., 1.91, 2.50)
- **Calculation**: `total_return = stake * decimal_odds`
- **Profit**: `profit = (decimal_odds - 1.0) * stake`
- **Examples**:
  - 1.91 odds on 1 unit: Total return = 1.91, Profit = 0.91
  - 2.50 odds on 1 unit: Total return = 2.50, Profit = 1.50

**Why Decimal Odds?**
PickVs uses decimal odds throughout because they clearly show both return and profit in a single number, making calculations simpler and more transparent than American or fractional odds.

### Odds at Pick Time
**odds_at_pick** is the decimal odds available to the user at the exact moment they submitted their prediction. This is critical because:
- Odds fluctuate as the event approaches
- Grading must use the odds locked in at submission, not current odds
- It ensures fairness (users can't claim better odds retroactively)

**Example**: User picks Lakers at 1.91 at 2:00 PM. By game time, odds are 1.85. The pick is still graded using 1.91.

---

## Performance Metrics

### Units / Result Units
A **unit** is a standardized betting stake used to measure performance consistently.

- **Stake Units**: The amount wagered per pick (PickVs always uses 1 unit per pick for standardization)
- **Result Units**: The profit/loss from a pick, expressed in units
  - **Win**: Positive result_units (0.91 for a 1.91 odds win)
  - **Loss**: -1.0 (always, when stake is 1 unit)
  - **Push**: 0.0 (no profit/loss)

**Why Units?**
Units normalize betting outcomes across picks with different odds, allowing fair comparison of betting skill regardless of how many picks someone makes.

---

### Total Units
**total_units** is the aggregate profit/loss across all of a user's graded picks.

- **Calculation**: Sum of all `result_units`
- **Formula**: `total_units = sum(result_units for all user's picks)`
- **Examples**:
  - 10 wins at 1.91 odds = 10 × 0.91 = +9.1 units
  - 10 losses = 10 × -1.0 = -10.0 units
  - Net = -0.9 units

**In Database**: Stored in `Users.total_units`, updated daily by `process-results-lambda`

---

### Total Wagered
**total_wagered** is the count of picks submitted (since each pick = 1 unit wagered).

- **Formula**: `total_wagered = count of all user's picks (regardless of outcome)`
- **Example**: User has made 25 picks → total_wagered = 25.0 units
- **Leaderboard Requirement**: Users must have `total_wagered >= 20` to appear in lifetime rankings

**In Database**: Stored in `Users.total_wagered`, updated daily by `process-results-lambda`

---

### ROI (Return on Investment)
**ROI** measures how efficiently a user's picks have performed.

- **Formula**: `ROI = (total_units / total_wagered) × 100` (percentage)
- **Interpretation**:
  - ROI = 10% means +10 units profit on 100 units wagered
  - ROI = -5% means -5 units loss on 100 units wagered
  - ROI = 0% means break-even (total_units ≈ 0)
- **Primary Leaderboard Sort**: Users ranked by highest ROI descending

**Example**:
- User: 25 picks, +3.5 units profit
- ROI = (3.5 / 25) × 100 = 14%

---

## Leaderboard Rankings

### Lifetime Rankings
The primary leaderboard tracking long-term betting skill.

- **Requirement**: Minimum 20 picks (`total_wagered >= 20`)
- **Sort**: Primary by ROI (descending), secondary by total_units (descending)
- **Purpose**: Identifies users with proven, consistent betting skill over time
- **Metric**: Represents return efficiency on every dollar wagered
- **Visible Field**: `picks_since_minimum` shows how many picks above the 20-pick threshold

---

### Weekly Rankings
A secondary leaderboard showing current momentum and recent form.

- **Requirement**: No minimum picks (resets weekly, new users can compete)
- **Time Window**: Last 7 days (resets Monday mornings)
- **Sort**: By total_units (descending)
- **Purpose**: Shows who's winning right now, encourages participation from new users
- **Visible Field**: Same metrics as lifetime (total_units, total_wagered, roi, accuracy)

---

## Accuracy Metrics

### Accuracy (Win Rate)
**accuracy** is the percentage of picks that resulted in a win (not a push).

- **Formula**: `accuracy = (picks_won / picks_graded) × 100` (percentage)
- **Picks Graded**: Picks with results (excludes pending picks and future events)
- **Example**:
  - 25 picks total: 15 wins, 8 losses, 2 pushes
  - accuracy = (15 / 25) × 100 = 60%
- **Not Used for Ranking**: Accuracy alone doesn't account for odds quality
  - High accuracy at bad odds (2.50+) = low ROI
  - Lower accuracy at good odds (1.50-1.91) = high ROI

**Example**: User picks at very high odds (lucky wins), 70% accuracy, but ROI = -15% (still losing money overall)

---

## Betting Terminology Quick Reference

| Term | Definition | Example |
|------|-----------|---------|
| **Pick** | Single prediction on one game market | Lakers moneyline at 1.91 |
| **Moneyline** | Predict the winner | Lakers vs Warriors → pick Lakers |
| **Spread** | Predict outcome with point handicap | Lakers -6.5 → Lakers win by 6+ |
| **Total** | Predict combined score over/under | Over 220.5 → combined score > 220.5 |
| **Decimal Odds** | Total return per unit wagered | 1.91 = $1 + $0.91 profit |
| **Push** | Exact tie (only in spread/total) | Lakers -6.5, final diff = 6.5 exactly |
| **Units** | Standardized stake (1 per pick) | 25 picks = 25 units wagered |
| **Result Units** | Profit/loss from a pick | Win: +0.91, Loss: -1.0, Push: 0.0 |
| **Total Units** | Net profit across all picks | +3.5 units (winning user) |
| **ROI** | Return on investment percentage | 14% ROI (3.5 units / 25 wagered) |
| **Accuracy** | Percentage of picks won | 60% (15 wins / 25 picks) |

---

## System-Specific Notes

### Why Standardize Stake to 1 Unit?
- **Fair Comparison**: Every pick counts equally in performance metrics
- **Simplicity**: No need to track different stake amounts per pick
- **Ranking**: All picks contribute equally to total_units and ROI calculations
- **Leaderboard Integrity**: Prevents "variance gaming" (betting more on uncertain picks)

### Why Decimal Odds?
- **Clarity**: Single number shows total return (e.g., 1.91 = $1.91 return on $1 wagered)
- **Calculation**: Profit = (odds - 1.0) × stake (vs. American odds which are asymmetric)
- **International Standard**: Used in Europe, Australia, and increasingly in online sportsbooks

### Grading Timeline
1. **Pick Submitted**: User makes pick at current odds → `odds_at_pick` is locked
2. **Game Plays**: Game occurs, result is recorded in `Games` table
3. **Daily Grading**: `process-results-lambda` runs at 9 AM, grades finished games
4. **Result Recorded**: `result_units` calculated and stored, user's leaderboard stats updated
5. **Next Day Rankings**: Leaderboard reflects the updated metrics

---

## Related Documentation

- [SCHEMA.md](SCHEMA.md) — Database structure for picks, odds, games, and users
- [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) — Pick grading logic and leaderboard calculation
- [LEADERBOARD_DESIGN.md](LEADERBOARD_DESIGN.md) — Detailed ranking algorithms
