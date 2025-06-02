import sys
from pathlib import Path
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTextEdit, QPushButton,
                             QLabel, QScrollArea, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QFont
from .message_widget import MessageWidget
from ui.ai_query_service import AIQueryService


class SignalHandler(QObject):
    """
    Handles signals for communication between threads.
    Ensures that operations interacting with the GUI from non-GUI threads
    are done safely via Qt's signal-slot mechanism.
    """
    missing_api_key = pyqtSignal(str)  # Emitted when an API key is found to be missing.
    response_received = pyqtSignal(str)  # Emitted when an AI response is received.

class ChatWindow(QMainWindow):
    """
    Main window for the chat interface.
    Handles UI setup, message display, user input, and communication with the AI client.
    """

    def __init__(self):
        """
        Initialize the chat window, signal handler, and AI client.
        """
        super().__init__()

        # Set up signal handler for cross-thread communication
        self.signal_handler = SignalHandler()
        self.signal_handler.response_received.connect(self.display_ai_response)
        self.signal_handler.missing_api_key.connect(self.handle_missing_api_key_error)

        # Initialize AI client
        try:
            self.ai_client = AIQueryService(signal_handler=self.signal_handler)
        except Exception as e:
            # Handle AIClient initialization failure gracefully, perhaps show an error message.
            # For now, we'll print and proceed, but the app might not be fully functional.
            print(f"Error initializing AIClient: {e}")
            # Potentially, disable sending messages or show a persistent error in the UI.
            # As a quick fix, one might add a label to the UI indicating the AI is unavailable.
            self.ai_client = None # Ensure it's defined

        # Build the user interface
        self.setup_ui()

        self.awaiting_api_key = False # Flag to indicate if app is waiting for user to input API key
        self.missing_key_name = ""    # Stores the name of the missing API key

    def setup_ui(self) -> None:
        """
        Configure the UI elements and overall layout of the chat window.
        """
        # Set window initial size and title
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle("AI Automation Assistant") # Added a window title

        # Apply a dark theme to the entire application
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #202123;
                color: #ffffff;
            }
        """)

        # Create central widget and main vertical layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0) # No space between main layout elements
        main_layout.setContentsMargins(20, 20, 20, 20) # Padding for the main window content

        # Top title label
        title_label = QLabel("AI Automation Assistant")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            QLabel {
                background-color: #202123; /* Match window bg */
                padding: 15px;
                border-bottom: 1px solid #444654; /* Separator line */
            }
        """)
        main_layout.addWidget(title_label)

        # Chat display area setup
        self.chat_area_widget = QWidget() # This widget will contain the message bubbles
        self.chat_layout = QVBoxLayout(self.chat_area_widget)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Messages stack from the top
        self.chat_layout.setSpacing(0) # No space between message bubbles themselves
        self.chat_layout.setContentsMargins(0, 0, 0, 0) # Let MessageWidget handle its own padding

        # Add chat_area_widget to a scroll area with custom scrollbar styling
        self.scroll_area = QScrollArea()
        self.scroll_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, # Take available horizontal space
            QSizePolicy.Policy.Expanding  # Take available vertical space (changed from Minimum)
        )
        self.scroll_area.setWidgetResizable(True) # Important for the inner widget to resize
        self.scroll_area.setWidget(self.chat_area_widget)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #202123; /* Match window bg */
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0px 2px 0px 0px; /* Small margin from the edge */
            }
            QScrollBar::handle:vertical {
                background-color: #666;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #888;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px; /* No arrows */
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none; /* No page jump background */
            }
        """)
        main_layout.addWidget(self.scroll_area, 1) # The '1' makes this widget expand

        # Bottom input container (ChatGPT-style input area)
        bottom_container = QWidget()
        bottom_container.setStyleSheet(
            "background-color: #202123; border: none;" # Match window bg
        )
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(10, 10, 10, 10) # Padding for the input area
        bottom_layout.setSpacing(10)

        # Input frame with rounded corners and border
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: #343541; /* Darker input area background */
                border: 1px solid #555;    /* Subtle border */
                border-radius: 12px;       /* Rounded corners */
            }
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(15, 10, 15, 10) # Padding inside the input frame
        input_layout.setSpacing(10)

        # QTextEdit for user message input
        self.message_input_edit = QTextEdit()
        self.message_input_edit.setPlaceholderText("Send a message...")
        self.min_input_height = 40  # Minimum height for one line of text
        self.max_input_height = 120 # Maximum height before scrolling within input
        self.message_input_edit.setFixedHeight(self.min_input_height)
        self.message_input_edit.setStyleSheet("""
            QTextEdit {
                background-color: transparent; /* Inherit from input_frame */
                border: none;
                color: #ffffff;
                font-size: 14px;
            }
            /* Scrollbar styling for the QTextEdit itself, if content exceeds max_input_height */
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0px 0px 0px 0px; /* No margin needed inside here */
            }
            QScrollBar::handle:vertical {
                background-color: #666;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #888;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        input_layout.addWidget(self.message_input_edit)
        self.message_input_edit.textChanged.connect(self.adjust_text_input_height)

        # Send button styled as a white circle with an arrow
        self.send_button = QPushButton("↑") # Up arrow for send
        self.send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_button.setFixedSize(32, 32) # Circular button size
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #000000;      /* Black arrow */
                border-radius: 16px; /* Half of size to make it circular */
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #e0e0e0; /* Slightly dimmer on hover */
            }
        """)
        self.send_button.clicked.connect(self.process_user_message)
        input_layout.addWidget(self.send_button)

        # Add the input_frame to the bottom layout
        bottom_layout.addWidget(input_frame)
        main_layout.addWidget(bottom_container)

        # Removed: main_layout.addStretch(0) as self.scroll_area with stretch factor 1 handles expansion.

        # Set the central widget for the QMainWindow
        self.setCentralWidget(central_widget)


    def adjust_text_input_height(self) -> None:
        """
        Adjust the height of the message input field based on its content,
        up to a maximum height.
        """
        # Calculate document height and add some padding
        document_height = self.message_input_edit.document().size().height()
        new_height = int(document_height) + 10 # 10 provides a little vertical padding

        # Clamp new_height between min and max predefined values
        if new_height < self.min_input_height:
            new_height = self.min_input_height
        elif new_height > self.max_input_height:
            new_height = self.max_input_height

        self.message_input_edit.setFixedHeight(new_height)

    def add_message_to_chat(self, message_text: str, is_user_message: bool = True) -> None:
        """
        Add a message bubble to the chat display area.

        Args:
            message_text (str): The text content of the message.
            is_user_message (bool): True if the message is from the user, False for AI.
        """
        message_widget = MessageWidget(message_text, is_user_message)

        # Limit the bubble width to 80% of the scroll area viewport for better readability
        # Ensure viewport exists and has a valid width
        viewport_width = self.scroll_area.viewport().width() if self.scroll_area.viewport() else self.scroll_area.width()
        bubble_max_width = int(viewport_width * 0.8)
        if bubble_max_width > 0 : # Ensure positive width
             message_widget.message_frame.setMaximumWidth(bubble_max_width)

        self.chat_layout.addWidget(message_widget)

        # Scroll to the bottom after a short delay to allow layout to update
        QTimer.singleShot(10, self._scroll_chat_to_bottom)

    def _scroll_chat_to_bottom(self) -> None:
        """
        Scroll the chat area to the bottom to show the latest message.
        """
        scrollbar = self.scroll_area.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())

    def resizeEvent(self, event) -> None:
        """
        Handle window resize events to adjust message bubble widths dynamically.

        Args:
            event: The resize event object from Qt.
        """
        super().resizeEvent(event) # Call base class implementation

        # Adjust each message bubble to occupy up to 80% of the new viewport width
        # Ensure viewport exists and has a valid width
        viewport_width = self.scroll_area.viewport().width() if self.scroll_area.viewport() else self.scroll_area.width()
        bubble_max_width = int(viewport_width * 0.8)

        if bubble_max_width > 0: # Ensure positive width
            for i in range(self.chat_layout.count()):
                item = self.chat_layout.itemAt(i)
                if item and item.widget() and hasattr(item.widget(), "message_frame"):
                    # item.widget() is the MessageWidget instance
                    item.widget().message_frame.setMaximumWidth(bubble_max_width)
        self.chat_layout.update() # Request a layout update

    def process_user_message(self) -> None: # Renamed from send_message for clarity
        """
        Handle sending the user's message: display it, and request AI response.
        Also handles API key submission if in that state.
        """
        # Retrieve and trim the user's input
        message_text = self.message_input_edit.toPlainText().strip()
        if not message_text:
            return # Do nothing if message is empty

        self.message_input_edit.clear()
        self.message_input_edit.setFixedHeight(self.min_input_height) # Reset input height

        # Disable the send button while processing
        self.send_button.setEnabled(False)

        if self.awaiting_api_key:
            # User is submitting an API key
            try:
                self.store_api_key(message_text) # The message_text is the API key
                self.awaiting_api_key = False
                self.message_input_edit.setPlaceholderText("Send a message...")
                self.add_message_to_chat(f"✅ API Key for '{self.missing_key_name}' saved. You can now send your message.", is_user_message=False)
                self.missing_key_name = ""
            except Exception as e:
                self.add_message_to_chat(f"❌ Error saving API Key: {e}", is_user_message=False)
            
            self.send_button.setEnabled(True) # Re-enable button after API key attempt
            return

        # Normal message processing flow
        if not self.ai_client:
            self.add_message_to_chat("AI client is not available. Please check configuration.", is_user_message=False)
            self.send_button.setEnabled(True)
            return

        self.add_message_to_chat(message_text, is_user_message=True)
        # Add a temporary "thinking" message for UX
        self.add_message_to_chat("AI is thinking...", is_user_message=False)

        # Fetch AI response in a separate thread to avoid freezing the GUI
        thread = threading.Thread(
            target=self.fetch_ai_response_in_thread,
            args=(message_text,)
        )
        thread.start()

    def fetch_ai_response_in_thread(self, user_message: str) -> None:
        """
        Retrieve the AI's response in a separate thread and emit signals.

        Args:
            user_message (str): The user's message text.
        """
        if not self.ai_client:
            self.signal_handler.response_received.emit("AI client not initialized.")
            return
        try:
            # ai_client.get_response_request will now return None if MissingAPIKeyError was signaled
            response_text = self.ai_client.get_response_request(user_message)
            
            if response_text is not None:
                # Only emit response_received if there's an actual response string to display.
                # This prevents displaying anything if AIQueryService returned None (e.g., after signaling a missing API key).
                self.signal_handler.response_received.emit(response_text)
            # If response_text is None, it implies that the missing_api_key signal was emitted by AIQueryService,
            # and ChatWindow.handle_missing_api_key_error has already been triggered to show the detailed prompt.

        # The MissingAPIKeyError exception is now fully handled within AIQueryService
        # if it originates from BlockGenerator. Thus, catching it here for that specific
        # case is no longer necessary.
        # Removed: except MissingAPIKeyError as e: ...
        except Exception as e:
            # This will catch other errors that might occur in get_response_request
            # or if ai_client itself is problematic.
            error_message = f"Error fetching AI response: {str(e)}"
            self.signal_handler.response_received.emit(error_message)

    def display_ai_response(self, response: str) -> None: # Renamed from print_response
        """
        Replace the 'AI is thinking...' placeholder with the actual AI response.

        Args:
            response (str): The AI's response text.
        """
        # Remove the last "thinking" message if present
        if self.chat_layout.count() > 0:
            last_item_widget = self.chat_layout.itemAt(self.chat_layout.count() - 1).widget()
            # A bit fragile, but common way to identify the "thinking" message.
            # Consider adding a property to MessageWidget or checking its text content if more robust check is needed.
            if isinstance(last_item_widget, MessageWidget) and not last_item_widget.is_user:
                 if last_item_widget.findChild(QLabel).text() == "AI is thinking...":
                    last_item_widget.deleteLater()
                    # self.chat_layout.removeWidget(last_item_widget) # Not strictly needed with deleteLater for layout items

        # Add the AI's actual response to the chat area
        self.add_message_to_chat(response, is_user_message=False)

        # Re-enable the send button
        self.send_button.setEnabled(True)
        self.message_input_edit.setFocus() # Return focus to input

    def handle_missing_api_key_error(self, key_name: str):
        """
        Handles the scenario where an API key is missing.
        Updates the UI to prompt the user for the key.

        Args:
            key_name (str): The name of the API key that is missing.
        """
        # Remove the "thinking" message if it was added
        if self.chat_layout.count() > 0:
            last_item_widget = self.chat_layout.itemAt(self.chat_layout.count() - 1).widget()
            if isinstance(last_item_widget, MessageWidget) and not last_item_widget.is_user:
                 if last_item_widget.findChild(QLabel).text() == "AI is thinking...": # Check if it's the placeholder
                    last_item_widget.deleteLater()

        self.missing_key_name = key_name
        error_message = f"🔑 The API key '{key_name}' is missing. Please enter it below and press send."
        self.add_message_to_chat(error_message, is_user_message=False)
        self.message_input_edit.setPlaceholderText(f"Enter API Key for '{key_name}'...")
        self.awaiting_api_key = True
        self.send_button.setEnabled(True) # Allow user to submit the key
        self.message_input_edit.setFocus()

    def store_api_key(self, api_key_value: str) -> None:
        """
        Saves the provided API key to the .env file.

        Args:
            api_key_value (str): The value of the API key to save.
        
        Raises:
            IOError: If there's an issue reading or writing the .env file.
        """
        key_to_save = self.missing_key_name # Use the stored key name
        if not key_to_save:
            # This case should ideally not happen if logic is correct
            raise ValueError("Missing key name was not set prior to saving API key.")

        env_file_path = Path(".env")
        lines = []

        try:
            if env_file_path.exists():
                with open(env_file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

            key_found_and_updated = False
            for i, line in enumerate(lines):
                if line.startswith(key_to_save + "="):
                    lines[i] = f"{key_to_save}={api_key_value}\n"
                    key_found_and_updated = True
                    break

            if not key_found_and_updated:
                lines.append(f"{key_to_save}={api_key_value}\n")

            with open(env_file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except IOError as e:
            # Propagate IO errors to be handled by the caller
            raise IOError(f"Failed to write API key to .env file: {e}")


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        # It's good to have a module-level docstring for the script too.
        # """Main application script for the AI Chat Window."""
        main_chat_window = ChatWindow()
        main_chat_window.show()
        sys.exit(app.exec())
    except ImportError as e: # Catch specific import error from top
        print(f"Critical Import Error: {e}. Application cannot start.")
        # Optionally, show a QMessageBox if QApplication can be initialized minimally
        # app = QApplication.instance() or QApplication(sys.argv) # Ensure app exists
        # QMessageBox.critical(None, "Startup Error", str(e))
    except Exception as e:
        # Generic fallback for other startup errors
        print(f"Failed to start the application (chat_window.py): {str(e)}")
        # Similar to above, a QMessageBox could be useful if GUI can be partly up.