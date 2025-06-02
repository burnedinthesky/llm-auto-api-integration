from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QSpacerItem
from PyQt6.QtCore import Qt

class MessageWidget(QFrame):
    """
    Widget to display a single chat message.
    It styles itself differently based on whether the message is from the user or the AI.
    """

    def __init__(self, text: str, is_user: bool = True, parent: QWidget = None):
        """
        Initialize the message widget.

        Args:
            text (str): The message text to display.
            signal_handler (SignalHandler): Handler for signals (not directly used in this class currently,
                                          but passed for potential future use or consistency).
            is_user (bool): If True, style as a user message; otherwise, style as an AI message.
            parent (QWidget, optional): Optional parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.is_user = is_user
        self._setup_ui(text)

    def _setup_ui(self, text: str) -> None:
        """
        Set up the UI components for the message widget.

        Args:
            text (str): The message text to display.
        """
        # Main layout for this widget, controlling overall padding of the message "row"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)  # Padding around the entire message widget
        layout.setSpacing(0)

        # Container to hold the message frame and spacer, allows for alignment
        container_widget = QWidget()
        container_layout = QHBoxLayout(container_widget)
        container_layout.setContentsMargins(10, 5, 10, 5) # Padding within the alignment container
        container_layout.setSpacing(0)

        # Frame that will hold the message text, this is the visual "bubble"
        message_frame = QFrame()
        message_frame_layout = QVBoxLayout(message_frame)
        message_frame_layout.setContentsMargins(15, 10, 15, 10) # Padding inside the bubble

        # Label to show the message text, with wrapping and selection enabled
        message_label = QLabel(text)
        message_label.setWordWrap(True)
        message_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # Expand horizontally to fill bubble
            QSizePolicy.Policy.Minimum,    # Take minimum vertical space needed
        )
        message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        message_frame_layout.addWidget(message_label)
        self.message_frame = message_frame # Store for potential external manipulation (e.g., width adjustment)

        if self.is_user:
            # Style for user messages: dark background with white text, aligned right
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
            # Style for AI messages: light background with black text, aligned left
            message_frame.setStyleSheet(
                """
                QFrame {
                    background-color: #f7f7f8;
                    border-radius: 10px;
                }
                """
            )
            message_label.setStyleSheet("color: #000000;")

            # Add spacer on the right, so AI's message aligns to the left
            container_layout.addWidget(message_frame)
            container_layout.addItem(
                QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            )

        layout.addWidget(container_widget)