# NexGen Bot: Development Guide

NexGen Bot is a multipurpose Discord bot designed to be a central hub for community management and engagement. It features a modular architecture that allows for easy expansion and maintenance.

## Project Structure

The bot follows a cog-based architecture, where each module is a self-contained unit (a "cog") that can be loaded, unloaded, or reloaded without restarting the entire bot.

```
/
├── .env                # Stores secret tokens and configuration
├── .gitignore          # Specifies files for Git to ignore
├── bot.py              # Main bot entry point
├── README.md           # This development guide
└── cogs/
    ├── core.py         # Core utility commands
    ├── project.py      # Project management system
    ├── events.py       # Event management module
    ├── giveaways.py    # Giveaway system
    ├── moderation.py   # Moderation suite
    └── engagement.py   # Fun and engagement commands
```

---

## Modules

### 1. Core Utility Module (`cogs/core.py`)

Handles essential bot functions and user onboarding.

#### Commands:

*   `/help`: Displays a dynamic list of all available commands and their descriptions.
*   `/serverinfo`: Shows statistics about the server (member count, creation date, etc.).
*   **Onboarding**: Automatically sends a welcome message with server rules and a role-selection guide to new members who join the server.

---

### 2. Project Management Module (`cogs/project.py`)

A system for teams to manage projects and tasks directly within Discord.

#### Commands:

*   `/project create <name> [description]`: Creates a new private channel and a dedicated role for the project. The user who creates the project is automatically assigned the role.
*   `/project update <name> <field> <new_value>`: Updates project details (e.g., description, status).
*   `/task add <project_name> <task_description>`: Adds a new task to a project's task list, which is managed in the project's channel.
*   `/task complete <project_name> <task_id>`: Marks a task as complete.

---

### 3. Event Management Module (`cogs/events.py`)

Create and manage server events with interactive RSVPs.

#### Features:

*   **Event Creation**:
    *   `/event create`: Opens a modal (pop-up form) for the user to fill in event details (title, description, date/time, location).
*   **RSVP System**:
    *   When an event is created, the bot sends an embed with "✅ Going" and "🤔 Interested" buttons.
    *   Members' RSVPs are tracked and can be viewed by the event organizer.
*   **Automatic Reminders**:
    *   The bot automatically sends a reminder to all "Going" and "Interested" members 24 hours and 1 hour before the event starts.

---

### 4. Giveaway System (`cogs/giveaways.py`)

Run timed giveaways and contests.

#### Commands:

*   `/giveaway start <duration> <winners> <prize>`: Starts a giveaway.
    *   `duration`: e.g., `1h`, `3d`
    *   `winners`: The number of winners.
    *   `prize`: The prize description.
*   **How it Works**:
    *   The bot posts an embed for the giveaway. Members enter by reacting with a 🎉 emoji.
    *   When the timer ends, the bot automatically selects the specified number of random winners from the participants, announces them, and DMs them.

---

### 5. Moderation Suite (`cogs/moderation.py`)

Standard tools for server moderators. These commands require the user to have the appropriate permissions.

#### Commands:

*   `/kick <member> [reason]`: Kicks a member from the server.
*   `/ban <member> [reason]`: Bans a member from the server.
*   `/purge <amount>`: Deletes a specified number of messages from the current channel.

---

### 6. Engagement Module (`cogs/engagement.py`)

Fun commands to keep the community active.

#### Commands:

*   `/poll <question> <option1> <option2> ...`: Creates a poll with up to 10 options. The bot adds reactions for each option so members can vote.
*   `/techfact`: Fetches and displays a random technology fact from an external API.
*   `/coinflip`: Flips a coin and returns "Heads" or "Tails".

---

## Setup and Running the Bot

1.  **Create a `.env` file** in the root directory with the following content:

    ```
    BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN
    GUILD_ID=YOUR_DISCORD_SERVER_ID
    OWNER_ID=YOUR_DISCORD_USER_ID
    ```

2.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```
    *(Note: A `requirements.txt` file should be created to list all necessary Python libraries, such as `discord.py` and `python-dotenv`)*

3.  **Run the bot**:
    ```bash
    python bot.py
    ```
