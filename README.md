# 📝 TODO List

## 🏗️ Development Tasks  
- [ ] Clans
- [ ] Block/ignore user
- [ ] Spectate live games
- [ ] Streaks
- [ ] Investigate how hard it is to mess with games (e.g., joining a random game)
- [ ] Search and Destroy
- [ ] Look into MySQL datatypes
- [ ] Clean unfinished games in Redis
- [ ] Save friendship data (e.g. how many games played together)
- [ ] Prevent emails going to spam
- [ ] Wrapper for socket errors
- [ ] Wrapper for notifications
- [ ] Game chat
- [ ] Fully custom maps
- [ ] Better status tracking (e.g. in game)
- [ ] Profile bio (special words get special styling)
- [ ] Finish replays
- [ ] Player count(maybe for each game mode?)
- [ ] Background music
- [ ] Leaderboard for account things (e.g. coins, amount of skins and background, net worth)
- [ ] Pause when switch tab(single player)
- [ ] Loading screen tips
- [ ] Lars heeft de replay opgegeten
- [ ] Frank Bakker rad
- [ ] Multiplayer gambling
- [ ] Ron VLAAAAAR


## 🔐 Account Management  
- [ ] Write the email for "Change password"  
- [ ] Allow users to delete their account  

## 🔧 Admin & Moderation

## 🎵 User Experience  
- [ ] Add music and sound effects

## 🐒 Before Release
- [ ] Add rate limits everywhere (also websockets)
- [ ] Make sure profile-dropdown menu is same on all pages
- [ ] Make sure all api endpoints have login requirements
- [ ] Make sure everything looks good on chromebook, laptop and Chrome browser
- [ ] Minify js and css

## 🫃🏿 Hopefully working
- [ ] Server crash if no place for food to spawn

## ✅ Completed  
- [x] Fix snake growing in the update after eating the food  
- [x] Implement server-side validation for snake games
- [x] Save games to Redis
- [x] Client only send direction
- [x] Fix sessions not expiring
- [x] Check snakes collisions after updating positions
- [x] Added countdown before game start
- [x] Added draws
- [x] Turn game update into one single socket message
- [x] Make wrapper functions for error handling and login requirements
- [x] Remove redundant code for client requests
- [x] Add username change
- [x] Add change password when logged in
- [x] Add profile picture support (no 18+ content)
- [x] Games history
- [x] Implement Redlock to prevent race conditions
- [x] Save game data + player stats
- [x] Show pfp of opp
- [x] Save usernames in Redis
- [x] Close rooms of finished games
- [x] Finish one vs one
- [x] Add general popup limit
- [x] Make snake head pfp
- [x] Cache pfp using query strings
- [x] Wrapper function for closing db cur and con
- [x] Live updates (e.g. when someone sends a friend request get live notify)
- [x] Friends
- [x] Split app.py over multiple files
- [x] Make api-endpoint better (e.g. /api/friends/requests)
- [x] Quick invite friend for 1v1
- [x] Player status
- [x] Resend invites and friend requests if user reloads page within ~5sec of receiving
- [x] Make email connections reconnected automatically
- [x] Add username sanitization
- [x] More unique mfa codes
- [x] Rate limit on flask_sid cookie
- [x] Random pfp on account creation
- [x] Add custom games
- [x] Clear localstorage on logout
- [x] One person logged in per account
- [x] On change password (if not logged in) close all sessions of that account
- [x] Might not need session["game_id"]
- [x] Kill tracking + k/d
- [x] Leaderboard
- [x] Feedback form
- [x] Lobby and custom game chat
- [x] Words in chat ending in -on to -on Jans
- [x] Single Player
- [x] Re-match feature for custom games
- [x] Fix matchmaking
- [x] One vs One snake growth
- [x] Create an admin dashboard with all session with rps and kritiek display
- [x] "Check spam" notification on verification
- [x] Issues with thumbnail saving
- [x] Snake and food skins


## 🚀 How to Deploy to Production

### 📌 Starting the Server

1. **Start Nginx**  
   ```sh
   sudo systemctl start nginx
   ```

2. **Start Gunicorn**  
   ```sh
   sudo systemctl start LarsVlaarSnake
   ```
   