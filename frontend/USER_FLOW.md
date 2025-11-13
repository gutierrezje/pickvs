PickVs (MVP) - User Flow & Wireframes

Owner: Product/Engineering
Status: Draft
Related Document: product_requirements.md

1. Overview

This document outlines the user's navigation path through the application and the key components on each page. This will serve as the primary guide for building the React frontend.

2. Page (View) Definitions

The React application will consist of 5 primary pages/views:

/register (Public): New user registration page.

/login (Public): Existing user login page.

/dashboard (Authenticated): The main page for logged-in users. Shows upcoming games and allows pick submission.

/leaderboard (Public): The main public leaderboard.

/my-picks (Authenticated): A page for a user to see their own pick history (pending and finished).

3. User Flow

This describes the journey a new user takes to become an active participant.

New User (Visitor) lands on the /leaderboard page. They see the rankings but can't participate.

User clicks "Register" -> navigates to /register.

User submits the registration form.

On Success: The backend returns a JWT. The frontend saves this token and navigates the user to /dashboard.

On Failure: An error message is displayed (e.g., "Email already in use").

Authenticated User is on /dashboard.

The frontend makes a GET /api/games/upcoming request (with the JWT).

The page displays a list of upcoming games.

User clicks on a game to expand it, selects a market (e.g., "Lakers -6.5"), and clicks "Submit Pick".

The frontend makes a POST /api/picks request.

On Success: A success message is shown ("Pick submitted!").

On Failure: An error is shown (e.g., "Game has already started").

User navigates to /my-picks to see their "Pending" pick.

The next day, after the game is finished and graded, the user checks /my-picks again to see their graded pick (e.g., "+0.91 units") and checks the /leaderboard to see their new rank.

4. Text-Based Wireframes

This outlines the key components needed for each page, which you can translate into React components.

Page: /register (Registration)

Components:

Navbar (Link to Login, Link to Leaderboard)

RegistrationForm (Container)

Input: username

Input: email

Input: password

Button: "Create Account"

ErrorMessage (Displays API errors)

Page: /login (Login)

Components:

Navbar (Link to Register, Link to Leaderboard)

LoginForm (Container)

Input: email

Input: password

Button: "Login"

ErrorMessage (Displays API errors)

Page: /dashboard (Pick Submission)

Components:

AuthenticatedNavbar (User: Model_Alpha, Link to LeaderDboard, Link to My Picks, Button: "Logout")

UpcomingGamesList (Container)

State: isLoading, error, games

Component: GameCard (maps over games array)

Props: game (object)

Displays: Home vs. Away, Game Time

Component: MarketRow (for Moneyline)

Button: Away Team (+120)

Button: Home Team (-140)

Component: MarketRow (for Spread)

Button: Away Team +2.5 (1.91)

Button: Home Team -2.5 (1.91)

Component: MarketRow (for Total)

Button: Over 220.5 (1.91)

Button: Under 220.5 (1.91)

PickConfirmationModal

Triggered on button click.

Displays: "Submit 1 Unit on Lakers -2.5 (1.91)?"

Button: "Confirm" (fires POST /api/picks)

Page: /leaderboard (Public Leaderboard)

Components:

Navbar (Link to Login/Register or Link to Dashboard if logged in)

LeaderboardControls

Toggle: "Sort by Units" / "Sort by ROI"

LeaderboardTable

State: isLoading, users

Columns: Rank, Username, Total Units, ROI, Total Bets

Component: UserRow (maps over users array)

Page: /my-picks (User's Pick History)

Components:

AuthenticatedNavbar

PickHistory (Container)

Toggle: "Pending Picks" / "Finished Picks"

PendingPicksList

Displays picks where result_units is null.

FinishedPicksList

Displays picks where result_units is not null.

Shows result (e.g., "+0.91" in green, "-1.00" in red).

MyStatsHeader

Displays: Total Units: 22.45, ROI: 8.2%