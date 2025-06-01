import os
import sys

# Ensure the parent directory is on the Python path so that BlockGenerator can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from blocks.block_generator import BlockGenerator
except ImportError:
    raise ImportError(
        "Failed to import BlockGenerator. "
        "Please verify that the 'blocks' directory exists and contains the necessary files."
    )


class AIClient:
    """Handle communication with the AI backend (BlockGenerator)."""

    def __init__(self):
        """
        Initialize the BlockGenerator instance.

        Raises:
            ImportError: If BlockGenerator initialization fails.
        """
        try:
            self.block_generator = BlockGenerator()
        except Exception as e:
            raise ImportError(f"Failed to initialize BlockGenerator: {e}")

    def get_response_request(self, user_message: str) -> str:
        """
        Obtain a response for the given user message.

        Args:
            user_message (str): The input message from the user.

        Returns:
            str: The generated response or an error message.
        """
        try:
            # Use BlockGenerator to process the request
            response = self.block_generator.generate_block(user_message)
            return response
        except Exception as e:
            # Return an error message if generation fails
            return f"Error processing request: {e}"