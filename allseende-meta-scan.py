import sys
import os
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QFrame,
    QMessageBox,
    QSizePolicy,
)
from PyQt5.QtGui import (
    QPixmap,
    QFontDatabase,
    QPainter,
    QPen,
    QColor,
    QMouseEvent,
    QPainterPath,
)
from PyQt5.QtCore import Qt, QRectF

import piexif
from PIL import Image

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

#  LIST OF ONLY NECESSARY METADATA AND THEIR DESCRIPTIONS
INTERESTING_TAGS = {
    ("0th", piexif.ImageIFD.Make): "Производитель устройства (камеры).",
    ("0th", piexif.ImageIFD.Model): "Конкретная модель устройства.",
    (
        "0th",
        piexif.ImageIFD.Software,
    ): "Программа, в которой обрабатывалось или сохранялось фото.",
    (
        "0th",
        piexif.ImageIFD.DateTime,
    ): "Точная дата и время последнего изменения файла.",
    ("Exif", piexif.ExifIFD.DateTimeOriginal): "Оригинальная дата и время съемки.",
    ("GPS", piexif.GPSIFD.GPSLatitude): "Географическая широта места съемки (GPS).",
    ("GPS", piexif.GPSIFD.GPSLongitude): "Географическая долгота места съемки (GPS).",
    ("Exif", piexif.ExifIFD.LensModel): "Модель использованного объектива.",
}


class MetaCleanerGUI(QWidget):
    def __init__(self):
        super().__init__()
        # Window Setting (Frameless + Translucent)
        self.setWindowFlags(Qt.FramelessWindowHint)
        # Важно для закругленных углов самого окна
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("ALLSEENDE SECURITY | META SCANNER")
        self.resize(1200, 850)
        self.setMinimumSize(1080, 750)
        self.setAcceptDrops(True)

        self.old_pos = None
        self.load_custom_font()
        self.apply_global_styles()

        self.current_file = None
        self.clean_image_obj = None

        # MAIN LAYOUT
        self.main_layout = QVBoxLayout(self)
        # Отступы нужны, чтобы рисовать тень или границы внутри paintEvent,
        # но в данном стиле мы рисуем вплотную к краю.
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # HEADER
        self.header_widget = QWidget()
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(40, 25, 20, 15)  # Увеличены отступы
        self.setup_header_content()
        self.main_layout.addWidget(self.header_widget)

        # BODY
        self.body_widget = QWidget()
        self.body_layout = QVBoxLayout(self.body_widget)
        self.body_layout.setContentsMargins(40, 10, 40, 40)
        self.body_layout.setSpacing(25)
        self.setup_body_content()
        self.main_layout.addWidget(self.body_widget)

        self.set_standby_mode()

    def setup_header_content(self):
        # 1. Logo
        self.logo_label = QLabel()
        self.load_logo()
        self.header_layout.addWidget(self.logo_label)

        # 2. Titles
        title_vbox = QVBoxLayout()
        self.title_main = QLabel("ALLSEENDE META SCAN")
        self.title_main.setStyleSheet(
            "font-size: 30px; font-weight: 900; color: #FFFFFF; letter-spacing: 5px; margin-left: 15px;"
        )

        self.title_sub = QLabel("ELIMINATING DIGITAL TRACES")
        self.title_sub.setStyleSheet(
            "font-size: 12px; color: #00F0FF; letter-spacing: 4px; margin-left: 22px; font-weight: bold;"
        )

        title_vbox.addWidget(self.title_main)
        title_vbox.addWidget(self.title_sub)
        self.header_layout.addLayout(title_vbox)
        self.header_layout.addStretch()

        # 3. Window Controls
        win_btns_layout = QHBoxLayout()
        win_btns_layout.setSpacing(10)
        btn_style = "QPushButton { background: transparent; color: #6A6D72; border: none; font-size: 20px; font-weight: bold; padding-bottom: 5px; }"

        self.btn_min = QPushButton("—")
        self.btn_min.setFixedSize(35, 35)
        self.btn_min.setCursor(Qt.PointingHandCursor)
        self.btn_min.setStyleSheet(btn_style + "QPushButton:hover { color: #00F0FF; }")
        self.btn_min.clicked.connect(self.showMinimized)

        self.btn_max = QPushButton("▢")
        self.btn_max.setFixedSize(35, 35)
        self.btn_max.setCursor(Qt.PointingHandCursor)
        self.btn_max.setStyleSheet(btn_style + "QPushButton:hover { color: #00F0FF; }")
        self.btn_max.clicked.connect(self.toggle_maximize)

        self.btn_close = QPushButton("×")
        self.btn_close.setFixedSize(35, 35)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet(
            btn_style + "QPushButton:hover { color: #FF3B30; }"
        )
        self.btn_close.clicked.connect(self.close)

        win_btns_layout.addWidget(self.btn_min)
        win_btns_layout.addWidget(self.btn_max)
        win_btns_layout.addWidget(self.btn_close)

        self.header_layout.addLayout(win_btns_layout)
        self.header_layout.setAlignment(win_btns_layout, Qt.AlignTop)

    def setup_body_content(self):
        content = QHBoxLayout()
        content.setSpacing(35)

        # LEFT PANEL
        left_box = QVBoxLayout()
        self.preview_label = QLabel("DROP IMAGE TO ANALYZE")
        self.preview_label.setObjectName("previewArea")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumWidth(550)
        left_box.addWidget(self.preview_label, 5)

        self.file_info_label = QLabel("READY FOR SCAN")
        self.file_info_label.setObjectName("fileInfo")
        self.file_info_label.setAlignment(Qt.AlignCenter)
        left_box.addWidget(self.file_info_label)

        self.select_btn = QPushButton("IMPORT FILE")
        self.select_btn.setObjectName("importBtn")
        self.select_btn.setFixedHeight(55)
        self.select_btn.setCursor(Qt.PointingHandCursor)
        self.select_btn.clicked.connect(self.select_photo)
        left_box.addWidget(self.select_btn)
        content.addLayout(left_box, 6)

        # RIGHT PANEL (METADATA)
        right_box = QVBoxLayout()
        self.meta_score_header = QLabel("SAFETY SCORE: STANDBY")
        self.meta_score_header.setStyleSheet(
            "font-size: 16px; color: #00F0FF; font-weight: 900; letter-spacing: 1px;"
        )
        right_box.addWidget(self.meta_score_header)

        self.meta_sub_header = QLabel("KEY DIGITAL FOOTPRINT MARKERS (TOP 8)")
        self.meta_sub_header.setStyleSheet(
            "font-size: 11px; color: #6A6D72; font-weight: bold; margin-bottom: 15px; letter-spacing: 0.5px;"
        )
        right_box.addWidget(self.meta_sub_header)

        # Scroll Area setup for dark background and rounded corners
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("metaScroll")

        # Internal card container
        self.meta_widget_container = QWidget()
        self.meta_widget_container.setObjectName("metaContainerWidget")
        self.meta_list = QVBoxLayout(self.meta_widget_container)
        self.meta_list.setAlignment(Qt.AlignTop)
        self.meta_list.setContentsMargins(15, 15, 15, 15)
        self.meta_list.setSpacing(8)

        self.scroll.setWidget(self.meta_widget_container)
        right_box.addWidget(self.scroll)
        content.addLayout(right_box, 4)
        self.body_layout.addLayout(content)

        # BOTTOM ACTIONS
        btns = QHBoxLayout()
        self.purge_btn = QPushButton("PURGE ALL DATA")
        self.purge_btn.setObjectName("purgeBtn")
        self.purge_btn.setFixedSize(240, 60)
        self.purge_btn.setCursor(Qt.PointingHandCursor)
        self.purge_btn.setEnabled(False)
        self.purge_btn.clicked.connect(self.clear_metadata)

        self.save_btn = QPushButton("SAVE CLEAN COPY")
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.setFixedSize(240, 60)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_copy)

        btns.addStretch()
        btns.addWidget(self.purge_btn)
        btns.addWidget(self.save_btn)
        self.body_layout.addLayout(btns)

    # Drawing a background with rounding
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Define the drawing area
        rect = QRectF(self.rect())
        # Corner radius (if not full screen)
        radius = 20.0 if not self.isMaximized() else 0.0

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        painter.fillPath(path, QColor("#0F1113"))

        painter.setClipPath(path)

        # Drawing a grid
        pen = QPen(QColor(0, 240, 255, 20))
        pen.setWidth(1)
        painter.setPen(pen)
        gap = 45
        for x in range(0, self.width(), gap):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), gap):
            painter.drawLine(0, y, self.width(), y)

    def apply_global_styles(self):
        self.setStyleSheet(
            """
            QWidget { color: #E1E4E8; font-family: 'Inter', sans-serif; }
            
            /* Стили левой панели */
            #previewArea { 
                background-color: rgba(26, 29, 33, 0.7); 
                border: 2px solid #2A2D32; 
                border-radius: 20px; 
                font-size: 18px; 
                color: #6A6D72; 
                font-weight: 900;
                letter-spacing: 2px;
            }
            #fileInfo { 
                font-size: 14px; color: #00F0FF; font-weight: bold; margin-top: 15px; letter-spacing: 1px;
            }
            #importBtn {
                background-color: rgba(255, 255, 255, 0.05); border: 2px solid #E1E4E8; border-radius: 12px; font-weight: 800; color: #E1E4E8; font-size: 14px; letter-spacing: 1px;
            }
            #importBtn:hover { background-color: #E1E4E8; color: #0F1113; border-color: #E1E4E8;}
            
            /* Стили правой панели метаданных (ТЕМНЫЙ ФОН И ЗАКРУГЛЕНИЯ) */
            #metaScroll { 
                border: none; 
                background: transparent; /* Сам скролл прозрачный */
            }
            #metaContainerWidget {
                background-color: rgba(26, 29, 33, 0.7); /* Темный фон контейнера */
                border: 2px solid #2A2D32; 
                border-radius: 20px; /* Закругленные углы */
            }
            
            /* Заглушка */
            #placeholderCard { border: none; background: transparent; }
            
            /* Кнопки действий */
            #purgeBtn {
                background-color: rgba(255, 59, 48, 0.1); border: 2px solid #FF3B30; color: #FF3B30; border-radius: 12px; font-weight: 900; font-size: 14px; letter-spacing: 1px;
            }
            #purgeBtn:disabled { border-color: #3A2020; color: #552A2A; background-color: transparent; }
            #purgeBtn:hover:enabled { background-color: #FF3B30; color: white; }

            #saveBtn {
                background-color: #00F0FF; color: #0F1113; border-radius: 12px; font-weight: 900; font-size: 14px; border: none; letter-spacing: 1px;
            }
            #saveBtn:disabled { background-color: #1A2525; color: #2A4040; }
            #saveBtn:hover:enabled { background-color: #66FFFF; }

            /* Скроллбар */
            QScrollBar:vertical { border: none; background: transparent; width: 8px; margin: 15px 0 15px 0; }
            QScrollBar::handle:vertical { background: #333; border-radius: 4px; min-height: 30px; }
            QScrollBar::handle:vertical:hover { background: #00F0FF; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
        """
        )

    def set_standby_mode(self):
        for i in reversed(range(self.meta_list.count())):
            widget = self.meta_list.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        placeholder = QFrame()
        placeholder.setObjectName("placeholderCard")
        ph_layout = QVBoxLayout(placeholder)
        ph_label = QLabel("WAITING FOR SCAN...")
        ph_label.setAlignment(Qt.AlignCenter)
        ph_label.setStyleSheet(
            "color: #6A6D72; font-size: 14px; font-weight: bold; letter-spacing: 2px; border: none; background: transparent;"
        )
        ph_layout.addWidget(ph_label)
        placeholder.setMinimumHeight(250)
        self.meta_list.addWidget(placeholder)

        self.meta_score_header.setText("SAFETY SCORE: STANDBY")
        self.meta_score_header.setStyleSheet(
            "font-size: 16px; color: #6A6D72; font-weight: 900; letter-spacing: 1px;"
        )

    def show_metadata(self):
        # Cleaning
        for i in reversed(range(self.meta_list.count())):
            widget = self.meta_list.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        found_count = 0
        try:
            exif_data = piexif.load(self.current_file)

            for (ifd_name, tag_id), description in INTERESTING_TAGS.items():
                if ifd_name in exif_data and tag_id in exif_data[ifd_name]:
                    value = exif_data[ifd_name][tag_id]

                    # GPS processing
                    if ifd_name == "GPS":
                        try:
                            # Simplified display of degrees
                            val_str = f"{value[0][0]}/{value[0][1]}°, {value[1][0]}/{value[1][1]}'..."
                        except:
                            val_str = "Complex GPS Data"
                    # String processing
                    elif isinstance(value, bytes):
                        try:
                            val_str = value.decode("utf-8").strip("\x00")
                        except:
                            try:
                                val_str = value.decode("utf-16").strip("\x00")
                            except:
                                val_str = "<Binary Data>"
                    else:
                        val_str = str(value)

                    # Get the readable name of the tag
                    try:
                        tag_name_readable = piexif.TAGS[ifd_name][tag_id]["name"]
                    except:
                        tag_name_readable = f"Tag {tag_id}"

                    if val_str and val_str != "Waiting...":
                        self.add_card(tag_name_readable, val_str, description)
                        found_count += 1

            if found_count == 0:
                self.add_card(
                    "CLEAN FILE",
                    "No key identifiable markers found in standard tags.",
                    "The file appears clean of common tracking data.",
                )
                self.meta_score_header.setText("SAFETY SCORE: SECURE (LIKELY)")
                self.meta_score_header.setStyleSheet(
                    "font-size: 16px; color: #00FF00; font-weight: 900; letter-spacing: 1px;"
                )

        except Exception as e:
            self.add_card(
                "ERROR", f"Scan failed: {str(e)}", "Could not parse file structure."
            )

    def add_card(self, title, val, tooltip_text):
        f = QFrame()
        # Card style inside dark block
        f.setStyleSheet(
            """
            QFrame {
                background: rgba(15, 17, 19, 0.6); 
                border-radius: 8px; 
                border: 1px solid rgba(0, 240, 255, 0.2);
            }
            QFrame:hover {
                border: 1px solid rgba(0, 240, 255, 0.6);
                background: rgba(15, 17, 19, 0.9); 
            }
        """
        )

        f.setToolTip(tooltip_text)

        l = QVBoxLayout(f)
        l.setContentsMargins(12, 10, 12, 10)
        l.setSpacing(4)
        t = QLabel(title.upper())
        t.setStyleSheet(
            "color: #00F0FF; font-size: 10px; font-weight: bold; border:none; background: transparent; letter-spacing: 0.5px;"
        )
        v = QLabel(val)
        v.setStyleSheet(
            "color: #E1E4E8; font-size: 12px; border:none; background: transparent; font-weight: 500;"
        )
        v.setWordWrap(True)
        l.addWidget(t)
        l.addWidget(v)
        self.meta_list.addWidget(f)

    # The rest of the logic
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and not self.isMaximized():

            if (
                event.pos().y() < 100
                or event.pos().x() < 100
                or event.pos().x() > self.width() - 100
            ):
                self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.old_pos:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.old_pos = None

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        self.update()  # Redraw corners

    def load_custom_font(self):
        f_path = os.path.join(PROJECT_DIR, "fonts", "InterVariable.ttf")
        if os.path.exists(f_path):
            QFontDatabase.addApplicationFont(f_path)

    def load_logo(self):
        l_path = os.path.join(PROJECT_DIR, "logo_photo_data.png")
        if os.path.exists(l_path):
            # LOGO ENLARGED TO 95x95
            px = QPixmap(l_path).scaled(
                95, 95, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.logo_label.setPixmap(px)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        path = e.mimeData().urls()[0].toLocalFile()
        self.load_image(path)

    def select_photo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Images (*.jpg *.jpeg *.png)"
        )
        if path:
            self.load_image(path)

    def load_image(self, path):
        self.current_file = path
        self.clean_image_obj = None
        self.save_btn.setEnabled(False)
        self.purge_btn.setEnabled(True)

        px = QPixmap(path)
        self.preview_label.setPixmap(
            px.scaled(
                self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        self.file_info_label.setText(f"SCANNING: {os.path.basename(path).upper()}")
        self.file_info_label.setStyleSheet(
            "color: #00F0FF; font-weight: 900; letter-spacing: 1px;"
        )

        self.meta_score_header.setText("SAFETY SCORE: VULNERABLE")
        self.meta_score_header.setStyleSheet(
            "font-size: 16px; color: #FF3B30; font-weight: 900; letter-spacing: 1px;"
        )

        self.show_metadata()

    def clear_metadata(self):
        if not self.current_file:
            return
        try:
            img = Image.open(self.current_file)
            data = list(img.getdata())
            self.clean_image_obj = Image.new(img.mode, img.size)
            self.clean_image_obj.putdata(data)

            self.purge_btn.setEnabled(False)
            self.save_btn.setEnabled(True)
            self.file_info_label.setText("PURGE COMPLETE. FILE IS ANONYMOUS.")
            self.file_info_label.setStyleSheet(
                "color: #FF3B30; font-weight: 900; letter-spacing: 1px;"
            )

            self.meta_score_header.setText("SAFETY SCORE: SECURE")
            self.meta_score_header.setStyleSheet(
                "font-size: 16px; color: #00FF00; font-weight: 900; letter-spacing: 1px;"
            )

            for i in reversed(range(self.meta_list.count())):
                widget = self.meta_list.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

            self.add_card(
                "STATUS",
                "All metadata markers removed from memory.",
                "File is ready for safe saving.",
            )

        except Exception as e:
            QMessageBox.critical(self, "System Error", f"Purge failed: {e}")

    def save_copy(self):
        if not self.clean_image_obj:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Secure Copy",
            "ALLSEENDE_SECURE_IMAGE.jpg",
            "JPG (*.jpg);;PNG (*.png)",
        )
        if path:
            self.clean_image_obj.save(path, "JPEG", quality=95)
            self.file_info_label.setText("SUCCESS: SECURE COPY SAVED")
            self.file_info_label.setStyleSheet(
                "color: #00FF00; font-weight: 900; letter-spacing: 1px;"
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MetaCleanerGUI()
    window.show()
    sys.exit(app.exec_())
