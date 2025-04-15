import sys
import os
import vlc
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QPushButton, QStackedWidget, QLineEdit,
    QSlider, QGraphicsOpacityEffect, QListWidgetItem
)
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation

light_theme = """
    QWidget {
        background-color: #f8f9fa;
        color: #212529;
        font-family: Arial;
    }
    QListWidget, QStackedWidget {
        background-color: #e9ecef;
        border: none;
    }
    QPushButton {
        background-color: #dee2e6;
        color: #212529;
        border: none;
        padding: 10px;
        border-radius: 8px;
    }
    QPushButton:hover {
        background-color: #ced4da;
    }
    QSlider::groove:horizontal {
        height: 6px;
        background: #ced4da;
        border-radius: 3px;
    }
    QSlider::handle:horizontal {
        background: #6c757d;
        width: 12px;
        margin: -5px 0;
        border-radius: 6px;
    }
    QLabel {
        color: #212529;
    }
"""

dark_theme = """
    QWidget {
        background-color: #2b2b2b;
        color: #f8f9fa;
        font-family: Arial;
    }
    QListWidget, QStackedWidget {
        background-color: #343a40;
        border: none;
    }
    QPushButton {
        background-color: #495057;
        color: white;
        border: none;
        padding: 10px;
        border-radius: 8px;
    }
    QPushButton:hover {
        background-color: #6c757d;
    }
    QSlider::groove:horizontal {
        height: 6px;
        background: #495057;
        border-radius: 3px;
    }
    QSlider::handle:horizontal {
        background: #adb5bd;
        width: 12px;
        margin: -5px 0;
        border-radius: 6px;
    }
    QLabel {
        color: #f8f9fa;
    }
"""

class SharkWave(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dark_mode = True
        self.apply_theme()
        self.setWindowTitle("SharkWave")
        self.setWindowIcon(QIcon("shark_icon.png"))
        self.setGeometry(100, 100, 1000, 600)

        self.music_folder = os.path.join(os.path.expanduser("~"), "SharkWave")
        os.makedirs(self.music_folder, exist_ok=True)

        self.player = vlc.MediaPlayer()
        self.current_track_index = -1
        self.track_paths = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_slider)
        self.current_position = 0
        self.slider_dragging = False

        self.initUI()

    def apply_theme(self):
        if self.dark_mode:
            self.setStyleSheet(dark_theme)
        else:
            self.setStyleSheet(light_theme)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def initUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        self.nav_list = QListWidget()
        self.nav_list.addItems(["Home", "Library", "Spotify", "YouTube", "Podcasts"])
        self.nav_list.setFixedWidth(150)
        self.nav_list.setFont(QFont("Arial", 12))
        self.nav_list.currentRowChanged.connect(self.display_page)

        self.pages = QStackedWidget()
        self.pages.addWidget(self.home_page())       # 0
        self.pages.addWidget(self.library_page())    # 1
        self.pages.addWidget(self.placeholder_page("Spotify"))   # 2
        self.pages.addWidget(self.placeholder_page("YouTube"))   # 3
        self.pages.addWidget(self.placeholder_page("Podcasts"))  # 4

        main_layout.addWidget(self.nav_list)
        main_layout.addWidget(self.pages)

    def home_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        label = QLabel("Welcome to SharkWave 🦈")
        label.setFont(QFont("Arial", 20))
        label.setAlignment(Qt.AlignCenter)

        self.theme_button = QPushButton("Switch Theme 🌗")
        self.theme_button.clicked.connect(self.toggle_theme)
        self.theme_button.setFixedWidth(200)
        self.theme_button.setCursor(Qt.PointingHandCursor)

        layout.addStretch()
        layout.addWidget(label)
        layout.addSpacing(20)
        layout.addWidget(self.theme_button, alignment=Qt.AlignCenter)
        layout.addStretch()

        page.setLayout(layout)
        return page

    def library_page(self):
        self.library_page_widget = QWidget()
        self.library_layout = QVBoxLayout()

        label = QLabel("Your Music Library")
        label.setFont(QFont("Arial", 16))
        label.setAlignment(Qt.AlignLeft)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by Artist, Album or Song")
        self.search_box.textChanged.connect(self.filter_library)

        self.music_list = QListWidget()
        self.music_list.setSpacing(2)
        self.music_list.itemDoubleClicked.connect(self.open_item)

        self.load_music_library()

        self.play_pause_button = QPushButton("▶️ Play")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)

        self.next_button = QPushButton("⏭ Next")
        self.next_button.clicked.connect(self.next_track)
        self.prev_button = QPushButton("⏮ Prev")
        self.prev_button.clicked.connect(self.prev_track)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.sliderMoved.connect(self.seek_music)
        self.slider.sliderPressed.connect(self.start_slider_drag)
        self.slider.sliderReleased.connect(self.stop_slider_drag)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setFont(QFont("Arial", 10))

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(200, 200)
        self.cover_label.setAlignment(Qt.AlignCenter)

        controls = QHBoxLayout()
        controls.addWidget(self.prev_button)
        controls.addWidget(self.play_pause_button)
        controls.addWidget(self.next_button)

        self.library_layout.addWidget(label)
        self.library_layout.addWidget(self.search_box)
        self.library_layout.addWidget(self.music_list)
        self.library_layout.addLayout(controls)
        self.library_layout.addWidget(self.slider)
        self.library_layout.addWidget(self.time_label)
        self.library_layout.addWidget(self.cover_label)
        self.library_page_widget.setLayout(self.library_layout)
        return self.library_page_widget

    def load_music_library(self):
        self.music_list.clear()
        self.track_paths = []

        artists = sorted(os.listdir(self.music_folder))
        for artist in artists:
            artist_path = os.path.join(self.music_folder, artist)
            if not os.path.isdir(artist_path):
                continue

            item = QListWidgetItem(artist)
            item.setData(Qt.UserRole, artist_path)
            self.music_list.addItem(item)

    def open_item(self, item):
        path = item.data(Qt.UserRole)
        if os.path.isdir(path):
            self.open_folder(path)
        elif os.path.isfile(path):
            self.play_music_from_list(item)

    def open_folder(self, path):
        self.music_list.clear()
        self.track_paths = []

        if os.path.isdir(path):
            albums = sorted(os.listdir(path))
            for album in albums:
                album_path = os.path.join(path, album)
                if os.path.isdir(album_path):
                    item = QListWidgetItem(album)
                    item.setData(Qt.UserRole, album_path)
                    self.music_list.addItem(item)
            self.load_songs(path)

    def load_songs(self, album_path):
        songs = sorted([f for f in os.listdir(album_path) if f.endswith(('.mp3', '.flac', '.wav'))])
        for song in songs:
            song_path = os.path.join(album_path, song)
            item = QListWidgetItem(song)
            item.setData(Qt.UserRole, song_path)
            self.music_list.addItem(item)
            self.track_paths.append(song_path)

    def play_music_from_list(self, item):
        path = item.data(Qt.UserRole)
        if path in self.track_paths:
            self.current_track_index = self.track_paths.index(path)
            self.current_position = 0
            self.play_music()

    def filter_library(self):
        search_text = self.search_box.text().lower()
        for i in range(self.music_list.count()):
            item = self.music_list.item(i)
            item.setHidden(False)
            if search_text and not any(search_text in part.lower() for part in item.text().split('/')):
                item.setHidden(True)

    def toggle_play_pause(self):
        if self.player.is_playing():
            self.current_position = self.player.get_time() // 1000
            self.player.pause()
            self.play_pause_button.setText("▶️ Play")
        else:
            if self.player.get_state() in [vlc.State.Ended, vlc.State.NothingSpecial]:
                self.play_music()
            else:
                self.player.play()
                self.player.set_time(self.current_position * 1000)
                self.timer.start(1000)
            self.play_pause_button.setText("⏸ Pause")

    def play_music(self):
        if 0 <= self.current_track_index < len(self.track_paths):
            path = self.track_paths[self.current_track_index]
            media = vlc.Media(path)
            self.player.set_media(media)
            self.player.play()

            QTimer.singleShot(200, lambda: self.player.set_time(self.current_position * 1000))

            self.slider.setValue(0)
            self.update_cover()
            self.timer.start(1000)
            self.play_pause_button.setText("⏸ Pause")

    def next_track(self):
        if self.current_track_index + 1 < len(self.track_paths):
            self.current_track_index += 1
            self.current_position = 0
            self.play_music()

    def prev_track(self):
        if self.player.get_time() // 1000 < 5:
            if self.current_track_index > 0:
                self.current_track_index -= 1
        self.current_position = 0
        self.play_music()

    def update_slider(self):
        if self.player.is_playing():
            current_pos = self.player.get_time() // 1000
            total_time = self.player.get_length() // 1000
            self.slider.setValue(current_pos)
            self.slider.setRange(0, total_time)
            self.time_label.setText(f"{self.format_time(current_pos)} / {self.format_time(total_time)}")

    def seek_music(self, position):
        if self.slider_dragging:
            self.player.set_time(position * 1000)

    def start_slider_drag(self):
        self.slider_dragging = True

    def stop_slider_drag(self):
        self.slider_dragging = False

    def format_time(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02}:{seconds:02}"

    def update_cover(self):
        album_image = self.get_album_cover()
        if album_image:
            pixmap = QPixmap(album_image)
            self.cover_label.setPixmap(pixmap)
            self.animate_cover()

    def get_album_cover(self):
        if 0 <= self.current_track_index < len(self.track_paths):
            current_track = self.track_paths[self.current_track_index]
            album_path = os.path.dirname(current_track)
            for file in os.listdir(album_path):
                if file.lower().endswith(('jpg', 'jpeg', 'png')):
                    return os.path.join(album_path, file)
        return None

    def animate_cover(self):
        opacity_effect = QGraphicsOpacityEffect(self.cover_label)
        self.cover_label.setGraphicsEffect(opacity_effect)
        animation = QPropertyAnimation(opacity_effect, b"opacity")
        animation.setDuration(1000)
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.start()

    def placeholder_page(self, name):
        page = QWidget()
        layout = QVBoxLayout()
        label = QLabel(f"{name} section (under development)")
        label.setFont(QFont("Arial", 16))
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        page.setLayout(layout)
        return page

    def display_page(self, index):
        self.pages.setCurrentIndex(index)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SharkWave()
    window.show()
    sys.exit(app.exec_())
