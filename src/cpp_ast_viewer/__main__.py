import sys

from PySide6.QtWidgets import QApplication

from cpp_ast_viewer.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
