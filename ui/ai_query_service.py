from exception.missing_api_key_error import MissingAPIKeyError
from blocks.block_generator import BlockGenerator

class AIQueryService:
    """
    Handles communication with the AI backend (specifically BlockGenerator)
    to process user messages and retrieve AI-generated responses.
    It also manages API key errors by signaling the UI if a handler is provided.
    """

    def __init__(self, signal_handler=None):
        """
        Initializes the AIQueryService.

        The actual AI model interface (BlockGenerator) is initialized lazily
        on the first request to optimize startup time.

        Args:
            signal_handler (QObject, optional): An object, typically from the UI,
                with a 'missing_api_key' signal. Used to notify the UI thread
                about missing API keys. Defaults to None.
        """
        self.block_generator: BlockGenerator | None = None  # Type hint for clarity
        self.signal_handler = signal_handler

    def get_response_request(self, user_message: str) -> str:
        """
        Obtains a response for the given user message from the AI backend.

        If the BlockGenerator has not been initialized yet, this method
        will initialize it. It handles potential MissingAPIKeyError by
        emitting a signal (if a signal_handler is configured) and returning
        a user-friendly error message. Other exceptions are also caught
        and returned as error messages.

        Args:
            user_message (str): The input message from the user.

        Returns:
            str: The AI-generated response, or a formatted error message
                 if an issue occurs during processing.
        """
        try:
            if not self.block_generator:
                # Lazy initialization of BlockGenerator on first use
                self.block_generator = BlockGenerator()
            
            response = self.block_generator.generate_block(user_message)
            return response
        except MissingAPIKeyError as e:
            # If a signal handler is provided, emit the missing API key signal.
            # This allows the UI to react, e.g., by prompting the user for the key.
            if self.signal_handler and hasattr(self.signal_handler, 'missing_api_key'):
                self.signal_handler.missing_api_key.emit(e.key_name)
                return None
            else:
                # Fallback if no signal handler is configured (though ChatWindow provides one)
                # This part ensures a message is still returned if signaling isn't possible.
                return f"❗ API key not set: {e.key_name}. (Signal handler not available or error in signaling)"
        except Exception as e:
            # Catch any other exceptions during AI processing and return an error message.
            # Logging the full exception here can be useful for debugging:
            # import logging
            # logging.exception("Error processing AI request")
            return f"Error processing request: {e}"