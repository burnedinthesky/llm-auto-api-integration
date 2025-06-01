import sys
from PyQt6.QtWidgets import QApplication
from ui.chat_window import ChatWindow

def main():
    try:
        app = QApplication(sys.argv)
        window = ChatWindow()
        window.show()
        return app.exec()
    except Exception as e:
        print(f"Failed to start the program: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
