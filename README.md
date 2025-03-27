# 📝 TODO List

## 🏗️ Development Tasks  
- [ ] Add custom games: invites are handled on the website
- [ ] Implement different game modes  
- [ ] Friends
- [ ] Investigate how hard it is to mess with games (e.g., joining a random game)  
- [ ] Implement multiplayer (ranked mode?)
- [ ] Make separate process for sending emails to remove workers bottleneck

## 🔐 Account Management  
- [ ] Create the email for "Change password"  
- [ ] Implement email change feature  
- [ ] Allow users to delete their account  
- [ ] Add profile picture support (no 18+ content)  

## 🔧 Admin & Moderation  
- [ ] Create an admin dashboard

## 🎵 User Experience  
- [ ] Add music and sound effects

## ✅ Completed  
- [x] Fix snake growing in the update after eating the food  
- [x] Implement server-side validation for snake games
- [x] Save games to Redis
- [x] Client only send direction
- [x] Fix sessions not expiring



## 🚀 How to Deploy to Production

### 📌 Starting the Server

1. **Start Nginx**  
   ```sh
   sudo systemctl start nginx
   ```

2. **Start the Workers**  
    Can only have as many workers as email addresses for now
   ```sh
   sudo systemctl start SnakeLarsVlaar@{0..4}
   ```

### 🛑 Stopping the Server

To stop the workers:  
```sh
sudo systemctl stop SnakeLarsVlaar@{0..4}
```

To stop Nginx:  
```sh
sudo systemctl stop nginx
```

### 🔄 Restarting Services

If you need to restart everything:  
```sh
sudo systemctl restart nginx
sudo systemctl restart SnakeLarsVlaar@{0..4}
```

💡 **Tip:** Check the status of the workers with:  
```sh
sudo systemctl status SnakeLarsVlaar@*
```