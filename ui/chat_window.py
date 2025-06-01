import sys
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, 
                             QLabel, QScrollArea, QFrame, QSizePolicy, QSpacerItem)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QFont

try:
    from ui.ai_client import AIClient
except Exception as e:
    raise ImportError(f"導入 AIClient 失敗: {e}")

class SignalHandler(QObject):
    """Handle signals for communication between threads."""

    response_received = pyqtSignal(str)


class MessageWidget(QFrame):
    """Widget to display a single chat message."""

    def __init__(self, text: str, is_user: bool = True, parent=None):
        """Initialize the message widget.

        Args:
            text (str): The message text to display.
            is_user (bool): If True, style as a user message.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.is_user = is_user
        self._setup_ui(text)

    def _setup_ui(self, text: str) -> None:
        """Set up the UI components for the message widget.

        Args:
            text (str): The message text to display.
        """
        # Main layout for this widget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        # Container to hold the message frame and spacer
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(10, 5, 10, 5)
        container_layout.setSpacing(0)

        # Frame that will hold the message text
        message_frame = QFrame()
        message_layout = QVBoxLayout(message_frame)
        message_layout.setContentsMargins(15, 10, 15, 10)

        # Label to show the message text, with wrapping and selection enabled
        message_label = QLabel(text)
        message_label.setWordWrap(True)
        message_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        message_layout.addWidget(message_label)
        self.message_frame = message_frame

        if self.is_user:
            # Style for user messages: dark background with white text
            message_frame.setStyleSheet(
                """
                QFrame {
                    background-color: #1a1a1a;
                    border-radius: 10px;
                }
                """
            )
            message_label.setStyleSheet("color: #ffffff;")

            # Add spacer on the left, so user's message aligns to the right
            container_layout.addItem(
                QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            )
            container_layout.addWidget(message_frame)
        else:
            # Style for non-user messages: light background with black text
            message_frame.setStyleSheet(
                """
                QFrame {
                    background-color: #f7f7f8;
                    border-radius: 10px;
                }
                """
            )
            message_label.setStyleSheet("color: #000000;")

            # Add spacer on the right, so non-user's message aligns to the left
            container_layout.addWidget(message_frame)
            container_layout.addItem(
                QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            )

        layout.addWidget(container)


class ChatWindow(QMainWindow):
    """Main window for the chat interface."""

    def __init__(self):
        """Initialize the chat window, signal handler, and AI client."""
        super().__init__()

        # Set up signal handler for cross-thread communication
        self.signal_handler = SignalHandler()
        self.signal_handler.response_received.connect(self.print_response)

        # Initialize AI client
        self.ai_client = AIClient()

        # Build the user interface
        self.setup_ui()

    def setup_ui(self) -> None:
        """Configure the UI elements and overall layout."""
        # Set window size
        self.setGeometry(100, 100, 800, 600)

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
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Top title label
        title_label = QLabel("AI Automation Assistant")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            QLabel {
                background-color: #202123;
                padding: 15px;
                border-bottom: 1px solid #444654;
            }
        """)
        main_layout.addWidget(title_label)

        # Chat display area
        self.chat_area = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_area)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(0)
        self.chat_layout.setContentsMargins(20, 20, 20, 20)

        # Add chat_area to a scroll area with custom scrollbar styling
        self.scroll_area = QScrollArea()
        self.scroll_area.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.chat_area)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #202123;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0px 2px 0px 0px;
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
        main_layout.addWidget(self.scroll_area, 1)
        main_layout.addStretch(0)

        # Bottom input container (ChatGPT-style input area)
        bottom_container = QWidget()
        bottom_container.setStyleSheet(
            "background-color: #202123; border: none;"
        )
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(10, 10, 10, 10)
        bottom_layout.setSpacing(10)

        # Input frame with rounded corners and border
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: #343541;
                border: 1px solid #555;
                border-radius: 12px;
            }
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(15, 10, 15, 10)
        input_layout.setSpacing(10)

        # QTextEdit for user message input
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Send a message...")
        self.min_input_height = 40
        self.max_input_height = 120
        self.message_input.setFixedHeight(self.min_input_height)
        self.message_input.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-size: 14px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0px 2px 0px 0px;
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
        input_layout.addWidget(self.message_input)
        self.message_input.textChanged.connect(self.adjust_input_height)

        # Send button styled as a white circle with an arrow
        self.send_button = QPushButton("↑")
        self.send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_button.setFixedSize(32, 32)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border-radius: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        # Add the input_frame to the bottom layout
        bottom_layout.addWidget(input_frame)
        main_layout.addWidget(bottom_container)

        # Set the central widget
        self.setCentralWidget(central_widget)


    def adjust_input_height(self) -> None:
        """Adjust the height of the input field based on its content."""
        # Calculate document height and add padding
        doc_height = self.message_input.document().size().height()
        new_height = int(doc_height) + 10

        # Clamp new_height between min and max values
        if new_height < self.min_input_height:
            new_height = self.min_input_height
        elif new_height > self.max_input_height:
            new_height = self.max_input_height

        self.message_input.setFixedHeight(new_height)

    def add_message(self, message: str, is_user: bool = True) -> None:
        """Add a message bubble to the chat area.

        Args:
            message (str): The text content of the message.
            is_user (bool): Whether the message is from the user (True) or AI (False).
        """
        message_widget = MessageWidget(message, is_user)

        # Limit the bubble width to 80% of the scroll area viewport
        bubble_width = int(self.scroll_area.viewport().width() * 0.8)
        message_widget.message_frame.setMaximumWidth(bubble_width)

        self.chat_layout.addWidget(message_widget)

        # Scroll to the bottom after a short delay
        QTimer.singleShot(10, self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> None:
        """Scroll the chat area to the bottom."""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def resizeEvent(self, event) -> None:
        """Handle window resize events to adjust message bubble widths.

        Args:
            event: The resize event object.
        """
        super().resizeEvent(event)

        # Adjust each message bubble to occupy up to 80% of the new width
        bubble_width = int(self.scroll_area.viewport().width() * 0.8)
        for i in range(self.chat_layout.count()):
            item = self.chat_layout.itemAt(i)
            if item and item.widget() and hasattr(item.widget(), "message_frame"):
                item.widget().message_frame.setMaximumWidth(bubble_width)
        self.chat_layout.update()

    def send_message(self, generate_code_after: bool = False) -> None:
        """Handle sending the user's message to the AI.

        Args:
            generate_code_after (bool): Placeholder for future functionality.
        """
        # Retrieve and trim the user's input
        message = self.message_input.toPlainText().strip()
        if not message:
            return

        # Disable the send button while waiting for a response
        self.send_button.setEnabled(False)

        # Display the user's message in the chat area
        self.add_message(message, is_user=True)
        self.message_input.clear()

        # Show a placeholder "thinking" message from the AI
        self.add_message("AI is thinking...", is_user=False)

        # Fetch AI response in a separate thread
        thread = threading.Thread(
            target=self.fetch_ai_response_in_thread,   
            args=(message,)
        )
        thread.start()

    def fetch_ai_response_in_thread(self, user_message: str) -> None:
        """Retrieve the AI's response in a separate thread.

        Args:
            user_message (str): The user's message text.
        """
        try:
            response = self.ai_client.get_response_request(user_message)
            self.signal_handler.response_received.emit(response)
        except Exception as e:
            error_message = f"Error fetching AI response: {str(e)}"
            self.signal_handler.response_received.emit(error_message)

    def print_response(self, response: str) -> None:
        """Replace the placeholder with the actual AI response.

        Args:
            response (str): The AI's response text.
        """
        # Remove the last "thinking" message if present
        if self.chat_layout.count() > 0:
            last_item = self.chat_layout.itemAt(self.chat_layout.count() - 1)
            if last_item and last_item.widget():
                last_item.widget().deleteLater()

        # Add the AI's actual response to the chat area
        self.add_message(response, is_user=False)

        # Re-enable the send button
        self.send_button.setEnabled(True)

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = ChatWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Failed to start this program in chat_window.py: {str(e)}")