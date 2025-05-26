import urllib.request
import json


def discord_send_message_API_runner(bot_token, channel_id, content, 
                                   username=None, avatar_url=None, 
                                   embeds=None, tts=False):
    """
    Send a message to a Discord channel using Discord API.
    
    Args:
        bot_token (str): Discord bot token for authentication.
        channel_id (str): The ID of the channel to send the message to.
        content (str): The message content to send (up to 2000 characters).
        username (str, optional): Override the default username of the webhook.
        avatar_url (str, optional): Override the default avatar of the webhook.
        embeds (list, optional): List of embed objects to send with the message.
        tts (bool, optional): Whether this is a TTS message. Defaults to False.
    
    Returns:
        dict: A dictionary containing:
            - success (bool): Whether the message was sent successfully
            - status_code (int): HTTP status code from the API response
            - message_id (str): ID of the sent message (if successful)
            - error (str): Error message (if unsuccessful)
    
    Raises:
        ValueError: If required parameters are missing or invalid.
        urllib.error.HTTPError: If the HTTP request fails.
    """
    if not bot_token or not channel_id or not content:
        raise ValueError("bot_token, channel_id, and content are required")
    
    if len(content) > 2000:
        raise ValueError("Message content cannot exceed 2000 characters")
    
    # Discord API endpoint for sending messages
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    
    # Prepare the payload
    payload = {
        "content": content,
        "tts": tts
    }
    
    if username:
        payload["username"] = username
    if avatar_url:
        payload["avatar_url"] = avatar_url
    if embeds:
        payload["embeds"] = embeds
    
    # Convert payload to JSON
    data = json.dumps(payload).encode('utf-8')
    
    # Prepare headers
    headers = {
        'Authorization': f'Bot {bot_token}',
        'Content-Type': 'application/json',
        'User-Agent': 'DiscordBot (https://github.com/discord/discord-api-docs, 1.0)'
    }
    
    try:
        # Create the request
        request = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        # Send the request
        with urllib.request.urlopen(request) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            
            return {
                "success": True,
                "status_code": response.status,
                "message_id": response_data.get("id"),
                "error": None
            }
            
    except urllib.error.HTTPError as e:
        error_response = json.loads(e.read().decode('utf-8'))
        return {
            "success": False,
            "status_code": e.code,
            "message_id": None,
            "error": error_response.get("message", f"HTTP {e.code} error")
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": None,
            "message_id": None,
            "error": str(e)
        }