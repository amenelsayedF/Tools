
import sys
from PyQt5.QtWidgets import QApplication
from gui import DorkGeneratorGUI

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = DorkGeneratorGUI()
    gui.show()
    sys.exit(app.exec_())
