# Twitch Task Manager Bot

This Twitch bot helps manage tasks and provides a Pomodoro timer for streamers and their community. It's designed to increase productivity and engagement during streams.

**Note: This project is currently under development and may undergo changes.**

## Setup

1. Clone the repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with the following variables:

   ```
   TWITCH_BOT_USERNAME=YourBotUsername
   TWITCH_OAUTH_TOKEN=oauth:your_oauth_token_here
   TWITCH_CHANNEL=YourChannelName
   ADMIN_USER=YourTwitchUsername
   ```

   - `TWITCH_BOT_USERNAME`: The username of your Twitch bot
   - `TWITCH_OAUTH_TOKEN`: OAuth token for your bot (get it from https://twitchapps.com/tmi/)
   - `TWITCH_CHANNEL`: The name of the Twitch channel where the bot will operate
   - `ADMIN_USER`: Your Twitch username (for admin commands)

4. Run the bot:
   ```
   python src/bot.py
   ```

## Commands

### Task Management

- `!task`: Display help message for task commands
- `!task add <description>`: Add a new task
- `!task remove <id>`: Remove a task
- `!task complete <id>`: Mark a task as complete
- `!task list`: Show your incomplete tasks
- `!task stats`: Display your task completion stats

### Pomodoro Timer (Admin only)

- `!timer`: Display help message for timer commands
- `!timer start`: Start the Pomodoro timer
- `!timer stop`: Stop the timer
- `!timer pause`: Pause the timer
- `!timer resume`: Resume the timer
- `!timer set <type> <minutes>`: Set the duration for a timer type
  - Types: `focus`, `short`, `long`

### Other Commands

- `!hi`: Bot responds with a greeting
- `!lurk`: Mark yourself as lurking
- `!lurkers`: Display the list of current lurkers

### Admin Commands

- `!task wipe <username>`: Remove all tasks for a specific user

## Features

- Task management system
- Pomodoro timer with customizable durations
- Daily stats reset and task cleanup
- Lurker tracking
- Visual task dashboard (displayed in the console)

## Contributing

This project is under active development. Feel free to submit issues or pull requests if you have suggestions or improvements.

## License

[MIT License](LICENSE)
