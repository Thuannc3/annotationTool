
import sys
from qtpy.QtWidgets import (
    QCheckBox,
    QApplication, QMainWindow, QLabel, QPushButton, QFileDialog,
    QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QComboBox,
    QHeaderView, QHBoxLayout, QMenuBar, QMenu, QAction, QSplitter, QScrollArea,
    QSpinBox
)
from qtpy.QtGui import QPixmap, QImage
from qtpy.QtCore import Qt
import cv2
import numpy as np

class ContourEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Contour Editor with QtPy")
        self.points = []
        self.selected_point = -1
        self.radius = 5
        self.mode = 'line'
        self.image = None
        self.zoom_factor = 1.0
        self.original_image = None
        self.is_annotated = False
        self.init_ui()

    def init_ui(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        load_action = QAction("Load Image", self)
        load_action.triggered.connect(self.load_image)
        file_menu.addAction(load_action)

        save_action = QAction("Save Output", self)
        save_action.triggered.connect(self.save_output)
        file_menu.addAction(save_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        control_layout = QHBoxLayout()
        self.hand_mode = QCheckBox("Hand Mode")
        self.hand_mode.setToolTip("Di chuyển ảnh bằng chuột trái khi bật chế độ này")
        control_layout.addWidget(self.hand_mode)
        btn_delete = QPushButton("Delete Selected Point")
        btn_delete.setToolTip("Xóa điểm đang chọn khỏi danh sách")
        btn_delete.setFixedWidth(150)
        btn_delete.clicked.connect(self.delete_selected_point)
        control_layout.addWidget(btn_delete)

        btn_zoom_in = QPushButton("Zoom In")
        btn_zoom_in.setToolTip("Phóng to ảnh")
        btn_zoom_in.setFixedWidth(100)
        btn_zoom_in.clicked.connect(self.zoom_in)
        control_layout.addWidget(btn_zoom_in)

        btn_zoom_out = QPushButton("Zoom Out")
        btn_zoom_out.setToolTip("Thu nhỏ ảnh")
        btn_zoom_out.setFixedWidth(100)
        btn_zoom_out.clicked.connect(self.zoom_out)
        control_layout.addWidget(btn_zoom_out)

        
        base_label = QLabel("Base Value:")
        control_layout.addWidget(base_label)


        self.base_value_box = QSpinBox()
        self.base_value_box.setRange(0, 255)
        self.base_value_box.setValue(0)
        self.base_value_box.setToolTip("Giá trị nền")
        control_layout.addWidget(self.base_value_box)

        
        layer_label = QLabel("Layer Value:")
        control_layout.addWidget(layer_label)


        self.layer_value_box = QSpinBox()
        self.layer_value_box.setRange(0, 255)
        self.layer_value_box.setValue(255)
        self.layer_value_box.setToolTip("Giá trị lớp")
        control_layout.addWidget(self.layer_value_box)

        btn_annotate = QPushButton("Annotate")
        btn_annotate.setToolTip("Gán giá trị lớp và nền theo contour")
        btn_annotate.setFixedWidth(100)
        btn_annotate.clicked.connect(self.annotate_image)
        control_layout.addWidget(btn_annotate)

        main_layout.addLayout(control_layout)

        splitter = QSplitter(Qt.Horizontal)

        self.view = QLabel()
        self.view.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        scroll_area = QScrollArea()
        self.scroll_area = scroll_area
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.view)
        splitter.addWidget(scroll_area)

        table_container = QWidget()
        table_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["X", "Y"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.itemChanged.connect(self.table_item_changed)
        self.table.setFixedWidth(200)
        table_layout.addWidget(self.table)

        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["line", "curve"])
        self.mode_selector.currentTextChanged.connect(self.change_mode)
        table_layout.addWidget(self.mode_selector)

        table_container.setLayout(table_layout)
        splitter.addWidget(table_container)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        main_layout.addWidget(splitter)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.view.mousePressEvent = self.mouse_press
        self.view.mouseMoveEvent = self.mouse_move
        self.view.mouseReleaseEvent = self.mouse_release

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.bmp)")
        if file_name:
            self.image = cv2.imread(file_name, cv2.IMREAD_GRAYSCALE)
            self.zoom_factor = 1.0
            self.update_display()

    def change_mode(self, text):
        self.mode = text
        self.update_display()

    def zoom_in(self):
        self.zoom_factor *= 1.2
        self.update_display()

    def zoom_out(self):
        self.zoom_factor /= 1.2
        self.update_display()

    def mouse_press(self, event):
        self.last_mouse_pos = event.pos()
        x, y = int(event.pos().x() / self.zoom_factor), int(event.pos().y() / self.zoom_factor)
        if event.button() == Qt.RightButton:
            self.points.append((x, y))
            self.update_table()
            self.update_display()
        elif event.button() == Qt.LeftButton:
            for i, (px, py) in enumerate(self.points):
                if abs(x - px) < self.radius and abs(y - py) < self.radius:
                    self.selected_point = i
                    return

    def mouse_move(self, event):
        if hasattr(self, 'hand_mode') and self.hand_mode.isChecked():
            delta = event.pos() - self.last_mouse_pos
            self.last_mouse_pos = event.pos()
            h_scroll = self.scroll_area.horizontalScrollBar()
            v_scroll = self.scroll_area.verticalScrollBar()
            h_scroll.setValue(h_scroll.value() - delta.x())
            v_scroll.setValue(v_scroll.value() - delta.y())
            return  # Make sure to return here to avoid executing the rest of the method

        if self.selected_point != -1:
            x, y = int(event.pos().x() / self.zoom_factor), int(event.pos().y() / self.zoom_factor)
            self.points[self.selected_point] = (x, y)
            self.update_table()
            self.update_display()

    def mouse_release(self, event):
        self.selected_point = -1

    def update_table(self):
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.points))
        for i, (x, y) in enumerate(self.points):
            self.table.setItem(i, 0, QTableWidgetItem(str(x)))
            self.table.setItem(i, 1, QTableWidgetItem(str(y)))
        self.table.blockSignals(False)

    def table_item_changed(self, item):
        row = item.row()
        try:
            x = int(self.table.item(row, 0).text())
            y = int(self.table.item(row, 1).text())
            self.points[row] = (x, y)
            self.update_display()
        except ValueError:
            pass

    def delete_selected_point(self):
        selected = self.table.currentRow()
        if 0 <= selected < len(self.points):
            self.points.pop(selected)
            self.update_table()
            self.update_display()

    def update_display(self):
        h_val = self.scroll_area.horizontalScrollBar().value() if hasattr(self, 'scroll_area') else 0
        v_val = self.scroll_area.verticalScrollBar().value() if hasattr(self, 'scroll_area') else 0
        if self.image is None:
            return
        img = cv2.cvtColor(self.image.copy(), cv2.COLOR_GRAY2RGB)
        for i, (x, y) in enumerate(self.points):
            cv2.circle(img, (x, y), self.radius, (0, 0, 255), -1)
            if self.mode == 'line' and i > 0:
                cv2.line(img, self.points[i-1], (x, y), (255, 0, 0), 2)
        if len(self.points) > 2:
            if self.mode == 'line':
                cv2.polylines(img, [np.array(self.points)], isClosed=True, color=(0, 255, 0), thickness=2)
            else:
                curve = cv2.approxPolyDP(np.array(self.points), epsilon=1.0, closed=True)
                cv2.polylines(img, [curve], isClosed=True, color=(0, 255, 0), thickness=2)
        h, w, ch = img.shape
        bytes_per_line = ch * w
        qt_img = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        scaled_img = qt_img.scaled(int(w * self.zoom_factor), int(h * self.zoom_factor), Qt.KeepAspectRatio)
        self.view.setPixmap(QPixmap.fromImage(scaled_img))
        if hasattr(self, 'scroll_area'):
            self.scroll_area.horizontalScrollBar().setValue(h_val)
            self.scroll_area.verticalScrollBar().setValue(v_val)

    def save_output(self):
        if self.image is None:
            return
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Image", "contour_output.png", "PNG Files (*.png)")
        if file_name:
            if self.is_annotated:
                cv2.imwrite(file_name, self.image)
                return
            img = cv2.cvtColor(self.image.copy(), cv2.COLOR_GRAY2RGB)
            for i, (x, y) in enumerate(self.points):
                cv2.circle(img, (x, y), self.radius, (0, 0, 255), -1)
                if self.mode == 'line' and i > 0:
                    cv2.line(img, self.points[i-1], (x, y), (255, 0, 0), 2)
            if len(self.points) > 2:
                if self.mode == 'line':
                    cv2.polylines(img, [np.array(self.points)], isClosed=True, color=(0, 255, 0), thickness=2)
                else:
                    curve = cv2.approxPolyDP(np.array(self.points), epsilon=1.0, closed=True)
                    cv2.polylines(img, [curve], isClosed=True, color=(0, 255, 0), thickness=2)
            cv2.imwrite(file_name, img)

    def annotate_image(self):
        if self.image is None or len(self.points) < 3:
            return

        if not self.is_annotated:
            # Lưu ảnh gốc
            self.original_image = self.image.copy()

            # Tạo mask từ contour
            mask = np.zeros_like(self.image, dtype=np.uint8)
            contour = np.array(self.points, dtype=np.int32)
            cv2.fillPoly(mask, [contour], 1)

            # Lấy giá trị từ ô nhập
            base_val = self.base_value_box.value()
            layer_val = self.layer_value_box.value()

            # Tạo ảnh annotate
            annotated = np.where(mask == 1, layer_val, base_val).astype(np.uint8)
            self.image = annotated
            self.is_annotated = True
        else:
            # Quay lại ảnh gốc
            self.image = self.original_image.copy()
            self.is_annotated = False

        self.update_display()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = ContourEditor()
    editor.show()
    sys.exit(app.exec_())
