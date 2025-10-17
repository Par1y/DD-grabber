import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from generator import Generator

def main():
    # 初始化Qt应用
    app = QApplication(sys.argv)
    
    # 创建Python后端实例
    generator = Generator()
    
    # 初始化QML引擎
    engine = QQmlApplicationEngine()
    
    # 将Generator实例注入QML上下文（QML中通过"generator"访问）
    engine.rootContext().setContextProperty("generator", generator)
    
    # 加载QML界面
    engine.load("main.qml")
    
    # 检查QML加载是否成功
    if not engine.rootObjects():
        sys.exit(-1)
    
    # 启动应用事件循环
    sys.exit(app.exec())

if __name__ == "__main__":
    main()