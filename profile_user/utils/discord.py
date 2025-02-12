import requests
import json

import environ
env = environ.Env()

DISCORD_BOT_TOKEN = env('DISCORD_BOT_ACCESS_TOKEN')
GUILD_ID = "1240992634210881607"  # Your Discord server ID
MEMBER_ROLE_ID = "1242066908803498045"  # The role that grants access
LIFETIME_ROLE_ID = "1242067075372023849"  

def get_discord_user_id(username):
    """Get user ID from their Discord username, searching through all members."""
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    members_url = f"https://discord.com/api/v9/guilds/{GUILD_ID}/members"
    params = {"limit": 1000}  # Discord API allows max 1000 per request
    members = []
    last_user_id = None  # For pagination

    while True:
        if last_user_id:
            params["after"] = last_user_id  # Fetch next page of users

        response = requests.get(members_url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Error fetching members: {response.status_code}, {response.text}")
            return None

        data = response.json()
        if not data:
            break  # No more members to fetch

        members.extend(data)

        # Check if the requested user is in the current batch
        for member in data:
            if "user" in member and member["user"].get("username") == username:
                return member["user"]["id"]

        # Set last user ID for pagination
        last_user_id = data[-1]["user"]["id"]

    return None

def add_role_to_user(discord_user_id, is_lifetime=False):
    """Assign a role to the user to grant access."""
    ROLE_ID = LIFETIME_ROLE_ID if is_lifetime else MEMBER_ROLE_ID
    url = f"https://discord.com/api/v9/guilds/{GUILD_ID}/members/{discord_user_id}"

    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {"roles": [ROLE_ID]}  # Ensure you pass a list of roles

    response = requests.patch(url, headers=headers, json=data)
    # print(response.status_code)
    # print(response.json())

    return response.status_code == 200

def remove_role_from_user(discord_user_name, is_lifetime=False):
    """Remove a role from the user."""
    discord_user_id = get_discord_user_id(discord_user_name)

    if discord_user_id is None:
        return False
    
    ROLE_ID = LIFETIME_ROLE_ID if is_lifetime else MEMBER_ROLE_ID
    url = f"https://discord.com/api/v9/guilds/{GUILD_ID}/members/{discord_user_id}/roles/{ROLE_ID}"

    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.delete(url, headers=headers)
    return response.status_code == 204 