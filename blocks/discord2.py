import os
import json
import urllib.request
import urllib.error


class DiscordClient:
    """
    DiscordClient is responsible for sending messages to a specific Discord channel
    using a bot token configured in a .env file.

    Attributes:
        app_id (str): Identifier for this application.
        bot_token (str): Discord bot token for authorization.
        channel_id (str): ID of the Discord channel to send messages to.
    """

    app_id = 'com.discord'

    def __init__(self, env_path: str = '.env'):
        """
        Initialize the DiscordClient by loading or prompting for configuration.

        Args:
            env_path (str): Path to the .env file. Defaults to '.env'.

        Raises:
            RuntimeError: If unable to read or write .env file.
        """
        self.env_path = env_path
        self._config = self._load_env()
        # Ensure bot token is present
        if 'DISCORD_BOT_TOKEN' not in self._config or not self._config['DISCORD_BOT_TOKEN']:
            token = input(
                "Enter your Discord Bot Token (get it from "
                "https://discord.com/developers/applications -> Your App -> Bot -> Token): "
            ).strip()
            if not token:
                raise RuntimeError("Discord Bot Token is required.")
            self._config['DISCORD_BOT_TOKEN'] = token
            self._append_env('DISCORD_BOT_TOKEN', token)
        # Ensure channel ID is present
        if 'DISCORD_CHANNEL_ID' not in self._config or not self._config['DISCORD_CHANNEL_ID']:
            cid = input(
                "Enter your Discord Channel ID (enable Developer Mode in Discord client, "
                "then Right-click channel -> Copy ID): "
            ).strip()
            if not cid:
                raise RuntimeError("Discord Channel ID is required.")
            self._config['DISCORD_CHANNEL_ID'] = cid
            self._append_env('DISCORD_CHANNEL_ID', cid)

        self.bot_token = self._config['DISCORD_BOT_TOKEN']
        self.channel_id = self._config['DISCORD_CHANNEL_ID']

    def _load_env(self) -> dict:
        """
        Load environment variables from the .env file.

        Returns:
            dict: A mapping of keys to values from the .env file.
        """
        config = {}
        if not os.path.isfile(self.env_path):
            # Create an empty .env if not exists
            open(self.env_path, 'a').close()
            return config

        with open(self.env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, val = line.split('=', 1)
                config[key.strip()] = val.strip()
        return config

    def _append_env(self, key: str, value: str) -> None:
        """
        Append a new key=value pair to the .env file.

        Args:
            key (str): The environment variable name.
            value (str): The environment variable value.
        """
        with open(self.env_path, 'a', encoding='utf-8') as f:
            f.write(f'\n{key}={value}')

    def send_message(self, content: str) -> dict:
        """
        Send a message to the configured Discord channel.

        Args:
            content (str): The message content to send.

        Returns:
            dict: The JSON response from Discord API on success.

        Raises:
            urllib.error.HTTPError: When the HTTP request fails with a status >= 400.
            urllib.error.URLError: When a connection error occurs.
            ValueError: If the response cannot be parsed as JSON.
        """
        url = f'https://discord.com/api/v10/channels/{self.channel_id}/messages'
        payload = json.dumps({'content': content}).encode('utf-8')
        headers = {
            'Authorization': f'Bot {self.bot_token}',
            'Content-Type': 'application/json',
            'User-Agent': f'{self.app_id} (https://github.com/yourrepo, 1.0)'
        }
        request = urllib.request.Request(url, data=payload, headers=headers, method='POST')

        try:
            with urllib.request.urlopen(request) as response:
                body = response.read().decode('utf-8')
                return json.loads(body)
        except urllib.error.HTTPError as e:
            # e.code, e.reason, e.read()
            error_body = e.read().decode('utf-8', errors='ignore')
            raise urllib.error.HTTPError(
                e.url, e.code, f"{e.reason}: {error_body}", e.headers, e.fp
            )
        except urllib.error.URLError as e:
            raise

block = DiscordClient()
block.send_message("Hello, Discord!")  # Example usage
