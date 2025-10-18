
import sys
from qtpy.QtWidgets import (
    QCheckBox,
    QApplication, QMainWindow, QLabel, QPushButton, QFileDialog,
    QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QComboBox,
    QHeaderView, QHBoxLayout, QMenuBar, QMenu, QAction, QSplitter, QScrollArea,
    QSpinBox, QSpacerItem, QSizePolicy
)
from qtpy.QtGui import QPixmap, QImage, QIcon
from qtpy.QtCore import Qt
import cv2
import numpy as np
from scipy.interpolate import splprep, splev
import json
from PyQt5.QtWidgets import QMessageBox

class ContourEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Contour Editor with QtPy - Multi Contours")
        self.contours = []  # list of dicts {name, points, layer_value}
        self.current_contour = None
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

        save_action = QAction("Save Image", self)
        save_action.triggered.connect(self.save_output)
        file_menu.addAction(save_action)

        # Save contours (to JSON)
        save_contours_action = QAction("Save Contours", self)
        save_contours_action.triggered.connect(self.save_contours)
        file_menu.addAction(save_contours_action)

        # Load contours (from JSON)
        load_contours_action = QAction("Load Contours", self)
        load_contours_action.triggered.connect(self.load_contours)
        file_menu.addAction(load_contours_action)

        help_menu = menu_bar.addMenu("Help")
        help_action = QAction("User Guide", self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        control_layout = QHBoxLayout()

        self.last_mouse_pos = None

        # Hand mode checkbox replaced by button with icon
        self.hand_mode = QCheckBox()
        self.hand_mode.setIcon(QIcon("images/hand.svg"))
        self.hand_mode.setToolTip("Hand Mode")
        self.hand_mode.stateChanged.connect(self.reset_pan_anchor)
        control_layout.addWidget(self.hand_mode)

        btn_zoom_in = QPushButton()
        btn_zoom_in.setIcon(QIcon("images/zoom-in.svg"))
        btn_zoom_in.setToolTip("Zoom In")
        btn_zoom_in.clicked.connect(self.zoom_in)
        control_layout.addWidget(btn_zoom_in)

        btn_zoom_out = QPushButton()
        btn_zoom_out.setIcon(QIcon("images/zoom-out.svg"))
        btn_zoom_out.setToolTip("Zoom Out")
        btn_zoom_out.clicked.connect(self.zoom_out)
        control_layout.addWidget(btn_zoom_out)

        control_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Add contour button (green)
        btn_add_contour = QPushButton("Add Contour")
        btn_add_contour.setStyleSheet("background-color: lightgreen;")
        btn_add_contour.clicked.connect(self.add_contour)
        control_layout.addWidget(btn_add_contour)

        self.contour_selector = QComboBox()
        self.contour_selector.setMinimumWidth(200)
        self.contour_selector.currentIndexChanged.connect(self.change_contour)
        control_layout.addWidget(self.contour_selector)

        btn_annotate = QPushButton("Annotate")
        btn_annotate.clicked.connect(self.annotate_image)
        control_layout.addWidget(btn_annotate)

        control_layout.addWidget(QLabel("Base Value:"))
        self.base_value_box = QSpinBox()
        self.base_value_box.setRange(0, 255)
        self.base_value_box.setValue(0)
        control_layout.addWidget(self.base_value_box)

        # Layer value moved up here
        control_layout.addWidget(QLabel("Layer Value:"))
        self.layer_value_box = QSpinBox()
        self.layer_value_box.setRange(0, 255)
        self.layer_value_box.valueChanged.connect(self.update_contour_values)
        control_layout.addWidget(self.layer_value_box)

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

        # Delete button moved here (red)
        btn_delete = QPushButton("Delete Selected Point")
        btn_delete.setStyleSheet("background-color: salmon;")
        btn_delete.clicked.connect(self.delete_selected_point)
        table_layout.addWidget(btn_delete)

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

    def add_contour(self):
        contour = {
            "name": f"Contour {len(self.contours)+1}",
            "points": [],
            "layer_value": 255,
            "mode": "line"   # mặc định line
        }
        self.contours.append(contour)
        self.current_contour = contour
        self.contour_selector.addItem(contour["name"])
        self.contour_selector.setCurrentIndex(len(self.contours)-1)
        self.update_table()

    def change_contour(self, index):
        if 0 <= index < len(self.contours):
            self.current_contour = self.contours[index]
            self.layer_value_box.setValue(self.current_contour["layer_value"])
            # sync mode_selector
            mode = self.current_contour.get("mode", "line")
            self.mode_selector.setCurrentText(mode)
            self.update_table()
            self.update_display()

    def update_contour_values(self):
        if self.current_contour:
            self.current_contour["layer_value"] = self.layer_value_box.value()

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.bmp)")
        if file_name:
            self.image = cv2.imread(file_name, cv2.IMREAD_GRAYSCALE)
            self.zoom_factor = 1.0
            self.update_display()

    def change_mode(self, text):
        if self.current_contour:
            self.current_contour["mode"] = text
            self.update_display()

    def zoom_in(self):
        self.zoom_factor *= 1.2
        self.update_display()

    def zoom_out(self):
        self.zoom_factor /= 1.2
        self.update_display()

    def mouse_press(self, event):
        if not self.current_contour:
            return
        self.last_mouse_pos = event.pos()
        x, y = int(event.pos().x() / self.zoom_factor), int(event.pos().y() / self.zoom_factor)
        if event.button() == Qt.RightButton:
            mode = self.mode_selector.currentText()
            self.current_contour["points"].append({"x": x, "y": y, "mode": mode})
            self.update_table()
            self.update_display()
        elif event.button() == Qt.LeftButton:
            for i, p in enumerate(self.current_contour["points"]):
                px, py = p["x"], p["y"]
                if abs(x - px) < self.radius and abs(y - py) < self.radius:
                    self.selected_point = i
                    return

    def mouse_move(self, event):
        if hasattr(self, 'hand_mode') and self.hand_mode.isChecked():
            # Nếu chưa có neo thì đặt neo rồi thoát, tránh delta bị None
            if self.last_mouse_pos is None:
                self.last_mouse_pos = event.pos()
                return
            delta = event.pos() - self.last_mouse_pos
            self.last_mouse_pos = event.pos()
            h_scroll = self.scroll_area.horizontalScrollBar()
            v_scroll = self.scroll_area.verticalScrollBar()
            h_scroll.setValue(h_scroll.value() - delta.x())
            v_scroll.setValue(v_scroll.value() - delta.y())
            return

        if self.current_contour and self.selected_point != -1:
            x, y = int(event.pos().x() / self.zoom_factor), int(event.pos().y() / self.zoom_factor)
            self.current_contour["points"][self.selected_point]["x"] = x
            self.current_contour["points"][self.selected_point]["y"] = y
            self.update_table()
            self.update_display()

    def mouse_release(self, event):
        self.last_mouse_pos = None
        self.selected_point = -1

    def update_table(self):
        self.table.blockSignals(True)
        if not self.current_contour:
            self.table.setRowCount(0)
            return
        points = self.current_contour["points"]
        self.table.setRowCount(len(points))
        for i, p in enumerate(points):
            self.table.setItem(i, 0, QTableWidgetItem(str(p["x"])))
            self.table.setItem(i, 1, QTableWidgetItem(str(p["y"])))
        self.table.blockSignals(False)

    def table_item_changed(self, item):
        if not self.current_contour:
            return
        row = item.row()
        try:
            x = int(self.table.item(row, 0).text())
            y = int(self.table.item(row, 1).text())
            self.current_contour["points"][row]["x"] = x
            self.current_contour["points"][row]["y"] = y
            self.update_display()
        except ValueError:
            pass

    def delete_selected_point(self):
        if not self.current_contour:
            return
        selected = self.table.currentRow()
        if 0 <= selected < len(self.current_contour["points"]):
            self.current_contour["points"].pop(selected)
            self.update_table()
            self.update_display()

    def update_display(self):
        if self.image is None:
            return
        img = cv2.cvtColor(self.image.copy(), cv2.COLOR_GRAY2RGB)
        for contour in self.contours:
            # Vẽ điểm và nhãn
            for i, p in enumerate(contour["points"]):
                cv2.circle(img, (p["x"], p["y"]), self.radius, (0, 0, 255), -1)
                cv2.putText(img, f"P{i+1}", (p["x"]+5, p["y"]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

            self.draw_contour_with_mixed_modes(contour, img)
            # Ghi tên contour
            if contour["points"]:
                cx, cy = contour["points"][0]["x"], contour["points"][0]["y"]
                cv2.putText(img, contour["name"], (cx+10, cy+10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)
        h, w, ch = img.shape
        bytes_per_line = ch * w
        qt_img = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        scaled_img = qt_img.scaled(int(w * self.zoom_factor), int(h * self.zoom_factor), Qt.KeepAspectRatio)
        self.view.setPixmap(QPixmap.fromImage(scaled_img))

    def save_output(self):
        if self.image is None:
            return
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Image", "mask.png", "PNG Files (*.png)")
        if file_name:
            cv2.imwrite(file_name, self.image)

    def reset_pan_anchor(self, state):
        self.last_mouse_pos = None

    def annotate_image(self):
        if self.image is None:
            return

        if not self.is_annotated:
            self.original_image = self.image.copy()
            annotated = np.full_like(self.image, self.base_value_box.value(), dtype=np.uint8)
            for contour in self.contours:
                poly = self.get_contour_polygon(contour)
                if len(poly) >= 3:
                    mask = np.zeros_like(self.image, dtype=np.uint8)
                    cv2.fillPoly(mask, [poly], 1)
                    annotated = np.where(mask == 1, contour["layer_value"], annotated)
            self.image = annotated
            self.is_annotated = True
        else:
            self.image = self.original_image.copy()
            self.is_annotated = False

        self.update_display()

    def save_contours(self):
        if not self.contours:
            return
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Contours", "contours.json", "JSON Files (*.json)")
        if file_name:
            with open(file_name, "w") as f:
                json.dump(self.contours, f, indent=2)

    def load_contours(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Contours", "", "JSON Files (*.json)")
        if file_name:
            with open(file_name, "r") as f:
                self.contours = json.load(f)
            if self.contours:
                self.current_contour = self.contours[0]
            self.contour_selector.clear()
            for c in self.contours:
                self.contour_selector.addItem(c["name"])
            self.update_table()
            self.update_display()

    def draw_quadratic_bezier(self, img, p0, p1, p2, color=(0,255,0), thickness=2):
        curve_pts = []
        for t in np.linspace(0, 1, 50):
            x = int((1-t)**2 * p0[0] + 2*(1-t)*t*p1[0] + t**2*p2[0])
            y = int((1-t)**2 * p0[1] + 2*(1-t)*t*p1[1] + t**2*p2[1])
            curve_pts.append((x, y))
        cv2.polylines(img, [np.array(curve_pts)], False, color, thickness)

    def draw_contour_with_mixed_modes(self, contour, img):
        pts = contour["points"]
        if len(pts) < 2:
            return

        i = 0
        while i < len(pts) - 1:
            p0 = (pts[i]["x"], pts[i]["y"])
            mode = pts[i+1]["mode"]

            if mode == "line":
                p1 = (pts[i+1]["x"], pts[i+1]["y"])
                cv2.line(img, p0, p1, (0,255,0), 2)
                i += 1

            elif mode == "curve":
                if i+2 < len(pts):
                    p1 = (pts[i+1]["x"], pts[i+1]["y"])
                    p2 = (pts[i+2]["x"], pts[i+2]["y"])
                    self.draw_quadratic_bezier(img, p0, p1, p2, (0,255,0), 2)
                    i += 2
                else:
                    # Không đủ điểm để vẽ cong → fallback line
                    p1 = (pts[i+1]["x"], pts[i+1]["y"])
                    cv2.line(img, p0, p1, (0,255,0), 2)
                    i += 1
        if len(pts) > 2:
            p_last = (pts[-1]["x"], pts[-1]["y"])
            p_first = (pts[0]["x"], pts[0]["y"])
            cv2.line(img, p_last, p_first, (0,255,0), 1)
    def get_contour_polygon(self, contour):
        pts = contour["points"]
        poly = []
        if len(pts) < 2:
            return np.array(poly, dtype=np.int32)

        i = 0
        while i < len(pts)-1:
            p0 = (pts[i]["x"], pts[i]["y"])
            mode = pts[i+1]["mode"]

            if mode == "line":
                p1 = (pts[i+1]["x"], pts[i+1]["y"])
                poly.append(p0)
                poly.append(p1)
                i += 1

            elif mode == "curve":
                if i+2 < len(pts):
                    p1 = (pts[i+1]["x"], pts[i+1]["y"])
                    p2 = (pts[i+2]["x"], pts[i+2]["y"])
                    for t in np.linspace(0,1,30):
                        x = int((1-t)**2*p0[0] + 2*(1-t)*t*p1[0] + t**2*p2[0])
                        y = int((1-t)**2*p0[1] + 2*(1-t)*t*p1[1] + t**2*p2[1])
                        poly.append((x,y))
                    i += 2
                else:
                    poly.append(p0)
                    i += 1

        # --- Đóng kín từ điểm cuối về điểm đầu ---
        if len(pts) > 2:
            p_last = (pts[-1]["x"], pts[-1]["y"])
            p_first = (pts[0]["x"], pts[0]["y"])
            mode = pts[0]["mode"]   # xét mode của điểm đầu

            if mode == "line":
                poly.append(p_last)
                poly.append(p_first)

            elif mode == "curve" and len(pts) >= 3:
                # lấy thêm điểm thứ 2 làm control
                p_ctrl = (pts[1]["x"], pts[1]["y"])
                for t in np.linspace(0,1,30):
                    x = int((1-t)**2*p_last[0] + 2*(1-t)*t*p_ctrl[0] + t**2*p_first[0])
                    y = int((1-t)**2*p_last[1] + 2*(1-t)*t*p_ctrl[1] + t**2*p_first[1])
                    poly.append((x,y))

        return np.array(poly, dtype=np.int32)


    def show_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Contour Editor - Help")
        msg.setText(
            "Contour Editor User Guide:\n\n"
            "- Right-click on image: Add point to current contour\n"
            "- Left-click + drag: Move point\n"
            "- Mode (line/curve): Choose between straight lines or smooth curves\n"
            "- Add Contour: Create a new contour\n"
            "- Delete Selected Point: Remove selected point from table\n"
            "- Base Value & Layer Value: Control annotation values\n"
            "- Annotate: Toggle between raw image and annotated mask\n"
            "- Hand Mode: Pan the image by dragging\n"
            "- Zoom In/Out: Scale the image view\n"
            "- Save Contours: Save current contours to JSON file\n"
            "- Load Contours: Load contours from JSON file\n"
        )
        msg.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = ContourEditor()
    editor.show()
    sys.exit(app.exec_())
