import os
import re
import threading
from typing import Optional
import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QLabel

from main import Analyzer, Object


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.source_path: Optional[str] = None
        self.cropped_directory: Optional[str] = None
        self.objects: Optional[list[Object]] = None
        self.__init_UI()

    def __init_UI(self):
        self.setWindowTitle('Space Data Analyzer')
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout(self)

        instruction_label = QLabel(
            'Выберите изображение, нажмите кнопку "разрезать изображение" и затем "анализировать".', self)
        layout.addWidget(instruction_label)

        crop_button = QPushButton('Разрезать изображение', self)
        crop_button.clicked.connect(self.__crop)
        crop_button.setStyleSheet('background-color: lightblue;')
        layout.addWidget(crop_button)

        analyze_button = QPushButton('Анализировать', self)
        analyze_button.clicked.connect(self.__analyze)
        analyze_button.setStyleSheet('background-color: lightgreen;')
        layout.addWidget(analyze_button)

        visualize_button = QPushButton('Визуализировать', self)
        visualize_button.clicked.connect(self.__visualize)
        visualize_button.setStyleSheet('background-color: lightcoral;')
        layout.addWidget(visualize_button)

    def __crop(self):
        self.source_path, _ = QFileDialog.getOpenFileName(
            self, 'Выберите исходное изображение', '', 'Изображения (*.jpg *.png)')
        if not self.source_path:
            QMessageBox.warning(self, 'Ошибка', 'Выберите исходное изображение')
            return

        self.cropped_directory = QFileDialog.getExistingDirectory(
            self, 'Выберите директорию для сохранения разрезанных изображений')
        if not self.cropped_directory:
            QMessageBox.warning(
                self, 'Ошибка', 'Выберите директорию для сохранения разрезанных изображений')
            return

        Analyzer.crop(self.source_path, self.cropped_directory, (100, 100))

    def __analyze(self):
        if not self.cropped_directory:
            self.cropped_directory = QFileDialog.getExistingDirectory(
                self, 'Выберите директорию с разрезанными изображениями')
            if not self.cropped_directory:
                QMessageBox.warning(
                    self, 'Ошибка', 'Выберите директорию с разрезанными изображениями')
                return

        self.objects = []

        threads = []
        for img_name in os.listdir(self.cropped_directory):
            thread = threading.Thread(
                target=self.__worker, args=(img_name,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        with open('statistic.txt', 'w') as file:
            for stat in self.objects:
                file.write(f'{stat}\n')

    def __worker(self, img_name):
        if not self.cropped_directory or self.objects is None:
            return

        match = re.findall(r'img(\d+)x(\d+)\.png', img_name)
        if match and len(match) == 1 and len(match[0]) == 2:
            x, y = int(match[0][0]), int(match[0][1])

            img_path = os.path.join(self.cropped_directory, img_name)
            img = cv2.imread(img_path)
            self.objects.extend(Analyzer.analyze(img, (x, y), 50))

    def __visualize(self):
        if not self.objects:
            QMessageBox.warning(self, 'Ошибка', 'Сначала выполните анализ')
            return

        if not self.source_path:
            self.source_path, _ = QFileDialog.getOpenFileName(
                self, 'Выберите исходное изображение', '', 'Изображения (*.jpg *.png)')
            if not self.source_path:
                QMessageBox.warning(self, 'Ошибка', 'Выберите исходное изображение')
                return

        img = cv2.imread(self.source_path)
        result = Analyzer.draw_overlay(img, self.objects, 20)
        cv2.imwrite('result.png', result)


if __name__ == "__main__":
    app = QApplication([])
    window = App()
    window.show()
    app.exec_()
