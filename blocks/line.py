import urllib.request
import urllib.parse
import json


def line_send_message_API_runner(channel_access_token, to, messages, 
                                notification_disabled=False):
    """
    Send messages to a LINE user, group, or room using LINE Messaging API.
    
    Args:
        channel_access_token (str): Channel access token for LINE Messaging API authentication.
        to (str): ID of the target recipient. Can be a user ID, group ID, or room ID.
        messages (list): List of message objects to send. Each message should be a dict
                        with 'type' and corresponding content fields. Maximum 5 messages.
                        Example: [{"type": "text", "text": "Hello World"}]
        notification_disabled (bool, optional): Set to True to disable push notification 
                                               for the message. Defaults to False.
    
    Returns:
        dict: A dictionary containing:
            - success (bool): Whether the messages were sent successfully
            - status_code (int): HTTP status code from the API response
            - sent_messages (int): Number of messages sent (if successful)
            - error (str): Error message (if unsuccessful)
            - error_details (dict): Detailed error information from LINE API (if unsuccessful)
    
    Raises:
        ValueError: If required parameters are missing or invalid.
        urllib.error.HTTPError: If the HTTP request fails.
    """
    if not channel_access_token or not to or not messages:
        raise ValueError("channel_access_token, to, and messages are required")
    
    if not isinstance(messages, list) or len(messages) == 0:
        raise ValueError("messages must be a non-empty list")
    
    if len(messages) > 5:
        raise ValueError("Maximum 5 messages can be sent at once")
    
    # Validate message structure
    for i, message in enumerate(messages):
        if not isinstance(message, dict) or 'type' not in message:
            raise ValueError(f"Message {i} must be a dict with 'type' field")
        
        if message['type'] == 'text' and 'text' not in message:
            raise ValueError(f"Text message {i} must have 'text' field")
        
        if message['type'] == 'text' and len(message['text']) > 5000:
            raise ValueError(f"Text message {i} cannot exceed 5000 characters")
    
    # LINE Messaging API endpoint
    url = "https://api.line.me/v2/bot/message/push"
    
    # Prepare the payload
    payload = {
        "to": to,
        "messages": messages,
        "notificationDisabled": notification_disabled
    }
    
    # Convert payload to JSON
    data = json.dumps(payload).encode('utf-8')
    
    # Prepare headers
    headers = {
        'Authorization': f'Bearer {channel_access_token}',
        'Content-Type': 'application/json',
        'User-Agent': 'LINE-Bot-SDK-Python/1.0'
    }
    
    try:
        # Create the request
        request = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        # Send the request
        with urllib.request.urlopen(request) as response:
            # LINE API returns empty body on success
            return {
                "success": True,
                "status_code": response.status,
                "sent_messages": len(messages),
                "error": None,
                "error_details": None
            }
            
    except urllib.error.HTTPError as e:
        try:
            error_response = json.loads(e.read().decode('utf-8'))
            error_message = error_response.get('message', f'HTTP {e.code} error')
            error_details = error_response.get('details', [])
        except:
            error_message = f'HTTP {e.code} error'
            error_details = None
            
        return {
            "success": False,
            "status_code": e.code,
            "sent_messages": 0,
            "error": error_message,
            "error_details": error_details
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": None,
            "sent_messages": 0,
            "error": str(e),
            "error_details": None
        }


def create_text_message(text):
    """
    Helper function to create a text message object for LINE API.
    
    Args:
        text (str): The text content of the message (max 5000 characters).
    
    Returns:
        dict: A text message object ready for LINE API.
    
    Raises:
        ValueError: If text is empty or exceeds character limit.
    """
    if not text or len(text.strip()) == 0:
        raise ValueError("Text cannot be empty")
    
    if len(text) > 5000:
        raise ValueError("Text message cannot exceed 5000 characters")
    
    return {
        "type": "text",
        "text": text
    }


def create_sticker_message(package_id, sticker_id):
    """
    Helper function to create a sticker message object for LINE API.
    
    Args:
        package_id (str): Package ID of the sticker.
        sticker_id (str): Sticker ID within the package.
    
    Returns:
        dict: A sticker message object ready for LINE API.
    
    Raises:
        ValueError: If package_id or sticker_id is empty.
    """
    if not package_id or not sticker_id:
        raise ValueError("package_id and sticker_id are required")
    
    return {
        "type": "sticker",
        "packageId": str(package_id),
        "stickerId": str(sticker_id)
    }