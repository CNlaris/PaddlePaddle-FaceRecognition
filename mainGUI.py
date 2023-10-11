import os
import sys
import cv2
import threading
import time
import subprocess
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QTextCodec, QProcess
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.uic import loadUi

QTextCodec.setCodecForLocale(QTextCodec.codecForName("UTF-8"))

class CameraThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.capture = cv2.VideoCapture(0)
        self.running = False
        self.frame = None

    def run(self):
        self.running = True
        while self.running:
            ret, frame = self.capture.read()
            if ret:
                self.frame = frame

    def stop(self):
        self.running = False
        self.capture.release()


class handleThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.capture = cv2.VideoCapture(0)
        self.running = False

    def run(self):
        self.running = True
        self.run_cmd()



    def run_cmd(self):
        """
        开启子线程，执行对应指令，控制台打印执行过程，然后将执行过程输出到textBrowser，然后返回子线程执行的状态码和执行返回的数据
        :return: 子线程状态码和执行结果
        """
        _cmd = 'python infer.py --image_path=temp/test.jpg'
        os.system(_cmd)

class Communicate(QObject):
    show_warning_signal = pyqtSignal()
    show_notification_signal = pyqtSignal()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = loadUi('mainGUI.ui', self)

        self.camera_thread = CameraThread()
        self.camera_thread.start()

        self.ui.pushButton.clicked.connect(self.take_photo)
        self.ui.pushButton_2.clicked.connect(self.run_inference)  # 修改这里

        self.timer = threading.Thread(target=self.update_label_3)
        self.timer.start()

        self.communicate = Communicate()
        self.communicate.show_warning_signal.connect(self.show_warning)
        self.communicate.show_notification_signal.connect(self.show_notification)

    def take_photo(self):
        threading.Thread(target=self.capture_photo).start()

    def capture_photo(self):
        if self.camera_thread.frame is not None:
            name = self.ui.lineEdit.text()
            if name is None or name == '':
                self.communicate.show_warning_signal.emit()
            else:
                file_name = 'face_db/' + name + '.jpg'
                cv2.imwrite(file_name, self.camera_thread.frame)
                self.update_label_4(file_name)
                self.communicate.show_notification_signal.emit()

    def show_warning(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("警告")
        msg_box.setText("请输入姓名")
        msg_box.exec_()

    def show_notification(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("通知")
        msg_box.setText("添加成功")
        msg_box.exec_()

    def update_label_3(self):
        while self.camera_thread.running:
            if self.camera_thread.frame is not None:
                start_time = time.time()
                pixmap = self.convert_frame_to_pixmap(self.camera_thread.frame)
                self.ui.label_3.setPixmap(pixmap)
                self.ui.label_3.setAlignment(Qt.AlignCenter)
                elapsed_time = time.time() - start_time
                time.sleep(max(0, 1 / 30 - elapsed_time))  # 控制帧率为30fps

    def update_label_4(self, image_path):
        pixmap = QPixmap(image_path)
        self.ui.label_4.setPixmap(pixmap)
        self.ui.label_4.setAlignment(Qt.AlignCenter)

    def convert_frame_to_pixmap(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame_rgb.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        return pixmap


    def run_inference(self):
        if self.camera_thread.frame is not None:
            file_name = 'temp/test.jpg'
            cv2.imwrite(file_name, self.camera_thread.frame)
            self.update_label_4(file_name)
            handle_thread = handleThread()
            handle_thread.run()


    def closeEvent(self, event):
        self.camera_thread.stop()
        self.camera_thread.join()  # 等待线程退出
        super().closeEvent(event)

    def update_text_browser(self, text):
        # 将文本添加到 textBrowser 中
        self.ui.textBrowser.append(text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
