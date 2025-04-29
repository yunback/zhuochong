import sys
from PyQt5.QtWidgets import QApplication
from desktop_pet import DesktopPet
import ctypes




if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    pet = DesktopPet()
    
    # 确保窗口关闭时应用程序退出

    
    sys.exit(app.exec_())