import sys, asyncio, re, bisect, aiohttp, os
import winrt.windows.media.control as wmc
from datetime import datetime, timezone
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                             QPushButton, QHBoxLayout, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QThread, Signal, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QGuiApplication

# --- Configuration & Helpers ---
CACHE_DIR = "lyrics_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

async def fetch_lyrics(artist, title, album, duration):
    """Fetches lyrics from LRCLIB with local file caching."""
    filename = f"{artist}_{title}".replace(" ", "_").lower() + ".lrc"
    filepath = os.path.join(CACHE_DIR, filename)

    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    url = "https://lrclib.net/api/get"
    params = {"artist_name": artist, "track_name": title, "album_name": album, "duration": duration}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    lyrics = data.get("syncedLyrics")
                    if lyrics:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(lyrics)
                        return lyrics
    except: return None
    return None

def parse_lrc(lrc_text):
    """Parses LRC into sorted list for Binary Search."""
    lyrics_data = []
    pattern = re.compile(r'\[(\d+):(\d+\.\d+)\](.*)')
    for line in lrc_text.splitlines():
        match = pattern.match(line)
        if match:
            m, s, text = int(match.group(1)), float(match.group(2)), match.group(3).strip()
            lyrics_data.append(((m * 60) + s, text))
    return sorted(lyrics_data)

# --- Logic Worker ---

class LyricsWorker(QThread):
    lyric_changed = Signal(str)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.main_loop())

    async def main_loop(self):
        manager = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
        last_id, parsed_lyrics, ts_list = "", [], []
        curr_text, is_fetching = "", False

        while True:
            session = manager.get_current_session()
            if session:
                # Filter for Spotify only
                app_id = session.source_app_user_model_id.lower()
                if "spotify" not in app_id:
                    if curr_text != "Not Spotify":
                        self.lyric_changed.emit("Not Spotify")
                        curr_text = "Not Spotify"
                    last_id, parsed_lyrics = "", []
                    await asyncio.sleep(1)
                    continue

                props = await session.try_get_media_properties_async()
                timeline = session.get_timeline_properties()
                song_id = f"{props.title}-{props.artist}"

                if song_id != last_id and not is_fetching:
                    last_id, is_fetching = song_id, True
                    self.lyric_changed.emit("Searching...")
                    raw = await fetch_lyrics(props.artist, props.title, props.album_title, timeline.end_time.total_seconds())
                    parsed_lyrics = parse_lrc(raw) if raw else []
                    ts_list = [x[0] for x in parsed_lyrics]
                    is_fetching, curr_text = False, ""

                if session.get_playback_info().playback_status == 4:
                    # Interpolation logic for smooth sync
                    time_diff = (datetime.now(timezone.utc) - timeline.last_updated_time.astimezone(timezone.utc)).total_seconds()
                    true_pos = timeline.position.total_seconds() + time_diff
                    idx = bisect.bisect_right(ts_list, true_pos)
                    new_lyric = parsed_lyrics[idx-1][1] if idx > 0 else "..."
                    if new_lyric != curr_text:
                        self.lyric_changed.emit(new_lyric)
                        curr_text = new_lyric
            else:
                if curr_text != "Waiting for Spotify...":
                    self.lyric_changed.emit("Waiting for Spotify...")
                    curr_text = "Waiting for Spotify..."
                last_id, parsed_lyrics, ts_list = "", [], []
            await asyncio.sleep(0.05)

# --- GUI with Animation & High Visibility ---

class FloatingLyrics(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0.0) 
        self.setMouseTracking(True) # Track mouse for hover effects
        
        # Main Layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Header with Close Button (Hidden by default)
        self.header_layout = QHBoxLayout()
        self.header_layout.addStretch()
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                color: rgba(255, 255, 255, 150);
                background-color: rgba(255, 0, 0, 100);
                border-radius: 15px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 200);
                color: white;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        self.close_btn.hide()
        self.header_layout.addWidget(self.close_btn)
        self.main_layout.addLayout(self.header_layout)

        # Lyrics Label
        self.label = QLabel("Spotify Sync")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            color: #FFFFFF; 
            font-size: 28px; 
            font-weight: 900;
            background-color: rgba(0, 0, 0, 40); /* Subtly dark for contrast */
            padding: 10px 40px;
            border-radius: 10px;
            font-family: 'Segoe UI', 'Arial Black', sans-serif;
        """)

        # Glow/Shadow for visibility on light backgrounds
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setXOffset(0)
        glow.setYOffset(0)
        glow.setColor(Qt.black)
        self.label.setGraphicsEffect(glow)

        self.main_layout.addWidget(self.label)
        self.setLayout(self.main_layout)

        # Animations
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(250)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.worker = LyricsWorker()
        self.worker.lyric_changed.connect(self.animate_text_change)
        self.worker.start()
        
        self.drag_pos = None
        self.is_auto_anchored = True
        self.next_text = ""
        self.update_position()

    def update_position(self):
        screen = QGuiApplication.primaryScreen().geometry()
        margin = 30
        self.move(screen.width() - self.width() - margin, margin)

    def animate_text_change(self, text):
        self.next_text = text
        self.anim.stop()
        self.anim.setStartValue(self.windowOpacity())
        self.anim.setEndValue(0.0)
        try: self.anim.finished.disconnect()
        except: pass
        self.anim.finished.connect(self.swap_text_and_fade_in)
        self.anim.start()

    def swap_text_and_fade_in(self):
        try: self.anim.finished.disconnect()
        except: pass
        self.label.setText(self.next_text)
        self.adjustSize()
        if self.is_auto_anchored: self.update_position()
        
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

    # Hover events to show/hide close button
    def enterEvent(self, event):
        self.close_btn.show()

    def leaveEvent(self, event):
        self.close_btn.hide()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = e.globalPosition().toPoint()
            self.is_auto_anchored = False

    def mouseMoveEvent(self, e):
        if self.drag_pos:
            delta = QPoint(e.globalPosition().toPoint() - self.drag_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.drag_pos = e.globalPosition().toPoint()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = FloatingLyrics()
    win.show()
    sys.exit(app.exec())
