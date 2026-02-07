# 🎵 Spotify Floating Synced Lyrics

A high-performance, transparent desktop widget that fetches and synchronizes lyrics in real-time with your Spotify playback. Built with Python, PySide6, and WinRT for millisecond-perfect accuracy.

## 🚀 Features

* **Real-time Synchronization**: Uses linear interpolation and binary search () to ensure lyrics match the audio perfectly, even between system clock updates.
* **Spotify Integration**: Exclusively monitors `spotify.exe` to provide a dedicated experience for Spotify users.
* **Smart Transparency**: A sleek, glassmorphic UI with a subtle drop shadow to ensure readability on both light and dark backgrounds.
* **Auto-Adjusting UI**: The widget automatically shrinks or grows based on lyric length and stays anchored to the top-right of your screen.
* **Local Caching**: Lyrics are stored locally in the `lyrics_cache` folder to enable instant loading for previously played songs.
* **Animated Transitions**: Smooth fade-in and fade-out animations for every lyric change.

## 🛠️ Installation

### For Users (Windows)

1. Go to the [Releases](https://www.google.com/search?q=https://github.com/Mayank-Creater/Spotify-Floating-Synced-Lyrics/releases) page.
2. Download the `SpotifyLyrics.zip` file.
3. Extract the folder and run `SpotifyLyrics.exe`.

### For Developers

1. Clone the repository:
```bash
git clone https://github.com/yourusername/repo.git

```


2. Install dependencies:
```bash
pip install -r requirements.txt

```


3. Run the application:
```bash
python main.py

```



## 📋 Requirements

* Windows 10 or 11 (required for WinRT APIs).
* Spotify Desktop App.

## 🚧 Roadmap & Contributions

We are dedicated to improving the user experience. Our current focus includes:

* **Expanding Database**: We are **constantly working on adding support for more song lyrics** to ensure even the most obscure tracks are covered.
* **Customization**: Adding a settings menu for font size and color preferences.
* **Multi-Platform**: Exploring support for macOS and Linux media controllers.

## ⚖️ Credits

* **Lyrics Provider**: Powered by [LRCLIB](https://lrclib.net/).
* **Built With**: PySide6, `aiohttp`, and `winrt`.
