# Zoom Assistant Manager

A Python GUI application for managing Zoom user assistants using OAuth device flow authentication.

## Features

- OAuth device flow authentication for Zoom
- Add multiple users as assistants to a target user
- Add target user as assistant to multiple users
- Real-time process logging
- User-friendly GUI interface

## Setup

1. **Create a Zoom App:**

   - Go to [Zoom Marketplace](https://marketplace.zoom.us/)
   - Click "Develop" > "Build App"
   - Choose "OAuth" app type
   - Fill in the required information
   - In "App Credentials", note your Client ID and Client Secret
   - In "Redirect URL for OAuth", add: `http://localhost:8080/callback`
   - In "Scopes", add: `user:read:list_assistants:admin`, `user:write:assistant:admin`, `user:read:user:admin`

2. **Configure the App:**

   ```bash
   cp config_template.py config.py
   # Edit config.py with your actual Client ID and Client Secret
   ```

3. **Run the Application:**

   **Easy Way:**

   ```bash
   ./launch_app.sh
   ```

   **Manual Way:**

   ```bash
   # Create and activate a virtual environment
   python3 -m venv .venv
   source .venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt

   # Then run the app
   python zoom_assistant_manager.py
   ```

## Usage

1. **Authentication:**

   - Ensure your Zoom App's Client ID and Client Secret are set in `config.py`
   - Click "Authenticate" button
   - A browser window will open for device flow authentication
   - Follow the instructions to complete authentication
   - The status will show your authenticated email in green

2. **Manage Assistants:**

   - Enter the target user's email in "Target User Email"
   - Enter assistant emails (one per line) in the text area
   - Click "Proceed" to start the process

3. **Process Flow:**
   - The app will add all users in the text area as assistants to the target user
   - Then it will add the target user as an assistant to each user in the text area
   - All actions are logged in real-time
   - If any operation fails, it will be logged and the process continues

## API Endpoints Used

- `POST /oauth/devicecode` - Start device flow authentication
- `POST /oauth/token` - Obtain access token via device flow
- `GET /users/me` - Get authenticated user info
- `GET /users/{email}` - Get info about any user by email
- `GET /users/{userId}/assistants` - List assistants for a user
- `POST /users/{userId}/assistants` - Add assistants to a user

## Requirements

- Python 3.7+
- tkinter (usually included with Python)
- requests
- Valid Zoom OAuth app credentials
- (Recommended) Run via `launch_app.sh` to auto-create a virtual environment and install dependencies

## Notes

- The application uses Zoom's device flow authentication for better security
- All operations are performed asynchronously to keep the UI responsive
- Detailed logging helps track the progress and identify any issues
- The app handles errors gracefully and continues processing remaining items
