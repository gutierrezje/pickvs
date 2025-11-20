# PickVs (MVP) - User Flow & Wireframes

## 1. Overview

This document outlines the user's navigation path through the application and the key components on each page. This will serve as the primary guide for building the React frontend.

## 2. Page (View) Definitions

The React application will consist of 5 primary pages/views:

| Route | Access | Purpose |
|-------|--------|---------|
| `/register` | Public | New user registration |
| `/login` | Public | Existing user login |
| `/dashboard` | Authenticated | Main hub: view upcoming games and submit picks |
| `/leaderboard` | Public | View all user rankings |
| `/my-picks` | Authenticated | View user's pick history (pending & finished) |

## 3. User Flow

This describes the journey a new user takes to become an active participant.

```
1. LANDING (Visitor)
   └─→ User lands on /leaderboard
       └─→ Views rankings (read-only)

2. REGISTRATION
   └─→ User clicks "Register"
       └─→ Navigates to /register
           └─→ Submits: username, email, password
               ├─ Success: Backend returns JWT → Save token → Redirect to /dashboard
               └─ Failure: Display error (e.g., "Email already in use")

3. PICK SUBMISSION (Authenticated)
   └─→ User on /dashboard
       └─→ Frontend fetches GET /api/games/upcoming (with JWT)
           └─→ Displays upcoming games with odds
               └─→ User selects market & clicks "Submit Pick"
                   └─→ Frontend calls POST /api/picks
                       ├─ Success: Show "Pick submitted!" message
                       └─ Failure: Show error (e.g., "Game has already started")

4. PICK TRACKING
   └─→ User navigates to /my-picks
       └─→ Views "Pending Picks" tab (result_units = NULL)
           └─→ After games finish & are graded (next day)
               └─→ Views "Finished Picks" tab (result_units = -1.0 or +X.XX)
                   └─→ Checks /leaderboard for new rank
```

## 4. Text-Based Wireframes

This outlines the key components needed for each page, which you can translate into React components.

---

### 4.1 `/register` (Registration)

**Components:**
- **Navbar**: Links to Login, Leaderboard
- **RegistrationForm**:
  - Input: username
  - Input: email
  - Input: password
  - Button: "Create Account"
- **ErrorMessage**: Displays API errors

---

### 4.2 `/login` (Login)

**Components:**
- **Navbar**: Links to Register, Leaderboard
- **LoginForm**:
  - Input: email
  - Input: password
  - Button: "Login"
- **ErrorMessage**: Displays API errors

---

### 4.3 `/dashboard` (Pick Submission)

**Components:**
- **AuthenticatedNavbar**:
  - Display username (e.g., "Model_Alpha")
  - Link to Leaderboard
  - Link to My Picks
  - Button: "Logout"

- **UpcomingGamesList** (State: isLoading, error, games):
  - **GameCard** (maps over games):
    - Displays: Home vs Away, Game Time
    - **MarketRow** (Moneyline): `[Away Team +120]` `[Home Team -140]`
    - **MarketRow** (Spread): `[Away +2.5 (1.91)]` `[Home -2.5 (1.91)]`
    - **MarketRow** (Total): `[Over 220.5 (1.91)]` `[Under 220.5 (1.91)]`

- **PickConfirmationModal**:
  - Triggered on market button click
  - Displays: "Submit 1 Unit on Lakers -2.5 (1.91)?"
  - Button: "Confirm" (fires POST /api/picks)

---

### 4.4 `/leaderboard` (Public Leaderboard)

**Components:**
- **Navbar**: Conditional links (Register/Login if not auth, Dashboard if auth)
- **LeaderboardControls**:
  - Sorting options: ROI, Total Units, Accuracy
- **LeaderboardTable** (State: isLoading, users):
  - Columns: Rank, Username, Total Units, ROI, Accuracy
  - **UserRow** (maps over users array)

---

### 4.5 `/my-picks` (User's Pick History)

**Components:**
- **AuthenticatedNavbar**
- **PickHistory** (Container):
  - Toggle: "Pending Picks" / "Finished Picks"

  - **PendingPicksList**: Shows picks where `result_units = NULL`

  - **FinishedPicksList**: Shows picks where `result_units ≠ NULL`
    - Color code: Green for wins (+X.XX), Red for losses (-1.00)

- **MyStatsHeader**:
  - Displays: Total Units, ROI %, Accuracy %


## Related Documentation
- [BACKEND_REQUIREMENTS.md](BACKEND_REQUIREMENTS.md)