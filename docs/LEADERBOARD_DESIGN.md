# PickVs - Hybrid Leaderboard Design

**Related Documents**: [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md), [SCHEMA.md](SCHEMA.md), [BACKEND_REQUIREMENTS.md](BACKEND_REQUIREMENTS.md)

---

## 1. Overview

The leaderboard system uses a **hybrid two-tiered approach** to address fairness issues and encourage different types of engagement:

1. **Lifetime Leaderboard** - Ranks users by long-term skill (ROI with minimum activity threshold)
2. **Weekly Leaderboard** - Ranks users by current momentum (last 7 days, no minimums)

This design solves the following problems:
- **Recency bias**: Early lucky streaks don't permanently rank #1
- **Late starter penalty**: New users can compete immediately on weekly board
- **Inactive players**: Encourages continuous participation
- **Fairness**: Both skill (lifetime) and form (weekly) are recognized

---

## 2. Leaderboard Specifications

### 2.1 Primary: Lifetime Leaderboard

**Endpoint**: `GET /api/leaderboard` (default)
**Cache**: 1 hour (recalculated every hour)
**Audience**: Long-term performers, overall rankings

#### Criteria

- **Minimum picks required**: 20 (approximately 3-4 weeks of activity)
- **Primary sort**: ROI (descending)
- **Secondary sort**: Total Units (descending) - break ties
- **Tertiary sort**: Username (ascending) - deterministic tiebreaker

#### Response Schema

```json
{
  "type": "lifetime",
  "min_picks_required": 20,
  "leaderboard": [
    {
      "rank": 1,
      "username": "sharp_bettor_42",
      "total_units": 150.50,
      "total_wagered": 100,
      "roi": 150.50,
      "accuracy": 0.65,
      "picks_since_minimum": 80
    }
  ]
}
```

**Field Descriptions:**
- `rank`: Position on leaderboard (1-indexed)
- `username`: User's display name
- `total_units`: Net profit/loss across all picks (sum of result_units)
- `total_wagered`: Total number of picks submitted
- `roi`: Return on investment percentage = (total_units / total_wagered) * 100
- `accuracy`: Win rate = (picks_won / total_wagered) * 100
- `picks_since_minimum`: Number of picks above the 20-pick threshold (shows dominance)

#### SQL Query

```sql
SELECT
    ROW_NUMBER() OVER (ORDER BY roi DESC, total_units DESC) as rank,
    username,
    total_units,
    total_wagered,
    ROUND((total_units / total_wagered)::numeric * 100, 2) as roi,
    ROUND(
        (COUNT(CASE WHEN result_units > 0 THEN 1 END)::numeric / total_wagered) * 100,
        2
    ) as accuracy,
    (total_wagered - 20) as picks_since_minimum
FROM Users
WHERE total_wagered >= 20
ORDER BY roi DESC, total_units DESC
```

**Explanation:**
- `ROI > 0 is good`: +50% means earning 50 cents per dollar wagered
- `Minimum threshold`: Filters out lucky early streaks (e.g., 2 wins out of 3 picks)
- `Picks_since_minimum`: Shows how dominant the leader is (100 picks vs exactly 20)

---

### 2.2 Secondary: Weekly Leaderboard

**Endpoint**: `GET /api/leaderboard?period=weekly`
**Alternative**: `GET /api/leaderboard?days=7` (or any custom number)
**Cache**: 30 minutes (faster updates to show momentum)
**Audience**: Current performers, new users, momentum chasers

#### Criteria

- **Time window**: Last 7 days (or custom days parameter)
- **Minimum picks**: None (fresh start every week)
- **Primary sort**: ROI (descending)
- **Secondary sort**: Total Units (descending)
- **Tertiary sort**: Username (ascending)

#### Response Schema

```json
{
  "type": "weekly",
  "period_days": 7,
  "period_start": "2025-11-10T00:00:00Z",
  "period_end": "2025-11-17T23:59:59Z",
  "leaderboard": [
    {
      "rank": 1,
      "username": "new_user_123",
      "total_units": 8.50,
      "total_wagered": 15,
      "roi": 56.67,
      "accuracy": 0.73
    }
  ]
}
```

#### SQL Query

```sql
WITH weekly_stats AS (
    SELECT
        p.user_id,
        u.username,
        SUM(p.result_units) as total_units,
        COUNT(*) as total_wagered,
        COUNT(CASE WHEN p.result_units > 0 THEN 1 END) as picks_won
    FROM Picks p
    JOIN Users u ON p.user_id = u.user_id
    WHERE p.created_at >= NOW() - INTERVAL '7 days'
    GROUP BY p.user_id, u.username
)
SELECT
    ROW_NUMBER() OVER (ORDER BY roi DESC, total_units DESC) as rank,
    username,
    total_units,
    total_wagered,
    ROUND((total_units / total_wagered)::numeric * 100, 2) as roi,
    ROUND((picks_won::numeric / total_wagered) * 100, 2) as accuracy
FROM (
    SELECT
        user_id,
        username,
        total_units,
        total_wagered,
        picks_won,
        CASE
            WHEN total_wagered > 0 THEN (total_units / total_wagered) * 100
            ELSE 0
        END as roi
    FROM weekly_stats
)
ORDER BY roi DESC, total_units DESC
```

---

## 3. Design Decisions & Rationale

### 3.1 Why Two Leaderboards?

| Aspect | Lifetime | Weekly |
|--------|----------|--------|
| **Use Case** | Prove long-term skill | Show current momentum |
| **Minimum Picks** | 20 | None |
| **Audience** | Serious bettors | New users, hot starters |
| **Time Horizon** | Season-long | Last 7 days |
| **Engagement** | "Can I make the main board?" | "Can I be this week's champ?" |

### 3.2 Why 20-Pick Minimum?

- **Statistical significance**: 20 picks provides decent sample size for noise filtering
- **Timeline**: ~3-4 weeks of daily picks (reasonable warmup)
- **Fairness**: Anyone can qualify within 1 month of signing up
- **Comparison**: Professional sports use 50+ picks; 20 is a compromise for MVP

### 3.3 Why ROI as Primary Sort?

- **Skill indicator**: ROI shows predictive ability per unit wagered
- **Fairness**: Doesn't penalize users who bet conservatively
- **Comparability**: Easy to understand (50% ROI = earn $0.50 per $1 wagered)
- **Alternative**: Total units (ignores volume) or accuracy (ignores odds)

### 3.4 Why No Minimum on Weekly Board?

- **Inclusivity**: New user joins Wednesday, competes immediately
- **Freshness**: Everyone resets each week (no permanent penalties)
- **Momentum**: Hot starters get recognition (incentivizes daily play)
- **Retention**: Low barrier to entry = higher engagement

---

## 4. Edge Cases & Handling

### 4.1 Division by Zero (0 total_wagered)

**Scenario**: User registered but made 0 picks

**Handling**:
- Exclude from both leaderboards (WHERE total_wagered > 0)
- Show on user profile as "No picks yet"

### 4.2 Exact ROI Ties

**Scenario**: Two users both have 50% ROI

**Tiebreaker order**:
1. Total units (higher is better)
2. Username (alphabetical, deterministic)

**Example**:
- User A: 50% ROI on +50 units
- User B: 50% ROI on +25 units
- **Result**: User A ranks higher

### 4.3 Negative ROI

**Scenario**: User has -20% ROI (losing money)

**Handling**: Include on leaderboard, rank lower than positive ROI users
- Sorting still works: -20% < 0% < +50%
- Transparency: Show losing streaks

### 4.4 Weekly Board with < 20 Picks Total

**Scenario**: User has 5 lifetime picks, all in last 7 days

**Handling**: Include on weekly board, exclude from lifetime
- User sees "You need 15 more lifetime picks to join the main leaderboard"
- Encourages continued play

---

## 5. Implementation Notes

### 5.1 Database Queries

**No schema changes required.** Both queries operate on existing tables:
- `Users` (total_units, total_wagered, roi)
- `Picks` (result_units, created_at)

### 5.2 Caching Strategy

**Lifetime Leaderboard**:
- Cache: 1 hour
- Rationale: Stats change slowly; rare picks from hundreds of users

**Weekly Leaderboard**:
- Cache: 30 minutes
- Rationale: More volatile; newer users want to see updates faster

**Implementation**: Use Redis or in-memory cache with TTL

### 5.3 Real-Time Updates (Post-Grading)

When `process-results-lambda` finishes grading picks:
1. Invalidate both cache keys
2. Frontend can optionally refetch immediately
3. Cache repopulates on next request

---

## 6. Frontend Considerations

### 6.1 UI Components

**Lifetime Tab**:
- Shows "You need 15 more picks to qualify" for users < 20 picks
- Highlight the user's position if they're on the board
- Show sorting options: ROI, Total Units, Accuracy

**Weekly Tab**:
- Always show user (even with 0 picks)
- Emphasize "Last 7 Days" prominently
- Show countdown to next week's reset

### 6.2 Sorting

```
GET /api/leaderboard?sort_by=roi        (default)
GET /api/leaderboard?sort_by=total_units
GET /api/leaderboard?sort_by=accuracy
```

---

## 7. Success Metrics

How to measure leaderboard effectiveness:

- **Engagement**: % of active users who check leaderboard weekly
- **Activation**: New users reaching 20-pick threshold within 4 weeks
- **Retention**: Users with 20+ picks who remain active after 6 weeks
- **Competition**: Multiple users in top 10 (not one dominant player)

---

## 8. Future Enhancements (Out of Scope)

- **Leaderboard by market**: "Best Moneyline Picker", "Best Spread Picker"
- **Streak tracking**: Current winning/losing streaks
- **Prediction graph**: ROI over time (trending up/down?)
- **Export stats**: Download CSV of leaderboard
- **Seasonal reset**: New season starts January, reset all stats

---

## Appendix: Example Scenarios

### Scenario A: Early Bird vs Late Starter

**Week 1:**
- User A: 8 wins, 2 losses on 10 picks (+6 units, 60% ROI)
- Status: NOT on leaderboard (needs 20 picks)

**Week 4:**
- User A: 65 wins, 35 losses on 100 picks (+5 units, 5% ROI)
- User B: 28 wins, 12 losses on 40 picks (just joined Week 3) (+10 units, 25% ROI)
- **Lifetime leaderboard**: User B ranks higher (25% ROI > 5% ROI)
- **Weekly leaderboard**: Both can compete; whoever performed better this week ranks higher

### Scenario B: Inactive Player Returns

**Initial**: User C ranks #5 with 50% ROI on 80 picks, then goes inactive

**8 weeks later**:
- User C still shows #5 on lifetime (no decay of past success)
- User C ranks low on weekly (no picks this week)
- If User C resumes and goes 0-5 this week, they drop on weekly but lifetime is unchanged

This is **desirable**: Rewards them for historical skill, but weekly shows they're out of form.

---

## Approval & Sign-Off

- [ ] Product approved
- [ ] Engineering reviewed
- [ ] Ready for Sprint 2 implementation

