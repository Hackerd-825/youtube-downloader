import os
import sys
import subprocess
import time

# ============================================================
#  AUTO-INSTALLATION DES MODULES MANQUANTS
# ============================================================

REQUIRED_MODULES = ["yt_dlp"]

def install_missing_modules():
    print("\nModules manquants détectés. Installation en cours...\n")
    for module in REQUIRED_MODULES:
        subprocess.call([sys.executable, "-m", "pip", "install", module])
    print("\nInstallation terminée. Redémarrage du programme...\n")
    time.sleep(1)
    os.execv(sys.executable, [sys.executable] + sys.argv)

missing = []
for module in REQUIRED_MODULES:
    try:
        __import__(module)
    except ImportError:
        missing.append(module)

if missing:
    install_missing_modules()

from yt_dlp import YoutubeDL

# ============================================================
#  FORMATS
# ============================================================

VIDEO_FORMATS = [
    ("mp4", "MP4"),
    ("mkv", "Matroska"),
    ("webm", "WebM"),
    ("avi", "AVI"),
    ("mov", "QuickTime"),
]

AUDIO_FORMATS = [
    ("mp3", "MP3"),
    ("m4a", "M4A"),
    ("opus", "Opus"),
    ("flac", "FLAC"),
    ("wav", "WAV"),
]

# ============================================================
#  UTILITAIRES
# ============================================================

def clear():
    os.system("cls")

def ask_path():
    clear()

    # Chemin par défaut : C:\Users\<User>\Downloads\YouTube_Downloads
    default_path = os.path.join(os.path.expanduser("~"), "Downloads", "YouTube_Downloads")

    print("📁 Où veux‑tu enregistrer les fichiers ?\n")
    print(f"Chemin par défaut : {default_path}")
    user_path = input("\n> ").strip()

    if user_path == "":
        user_path = default_path

    user_path = os.path.expanduser(user_path)

    if not os.path.exists(user_path):
        os.makedirs(user_path, exist_ok=True)

    return user_path


def main_menu():
    clear()
    print("=== YouTube Downloader (Windows) ===\n")
    print("1 - Télécharger une/des VIDÉO(s)")
    print("2 - Télécharger une/des MUSIQUE(s)")
    print("3 - Quitter\n")
    return input("Choix : ").strip()


def choose_format(mode):
    clear()
    if mode == "video":
        print("Choisis le format VIDÉO :\n")
        formats = VIDEO_FORMATS
    else:
        print("Choisis le format AUDIO :\n")
        formats = AUDIO_FORMATS

    for i, (ext, label) in enumerate(formats, start=1):
        print(f"{i} - {ext} ({label})")

    while True:
        choice = input("\nChoix : ").strip()
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(formats):
                return formats[idx - 1][0]
        print("Choix invalide.")


def analyze_url(url):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "ignoreerrors": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def build_entries(info):
    if info.get("_type") is None:
        return [info]

    entries = info.get("entries") or []
    return [e for e in entries if e]


def build_ydl_opts(mode, out_dir, ext):
    base_outtmpl = os.path.join(out_dir, "%(title)s.%(ext)s")

    if mode == "video":
        return {
            "outtmpl": base_outtmpl,
            "format": "bestvideo+bestaudio/best",
            "ignoreerrors": True,
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": ext,
                }
            ],
        }
    else:
        return {
            "outtmpl": base_outtmpl,
            "format": "bestaudio/best",
            "ignoreerrors": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": ext,
                    "preferredquality": "0",
                }
            ],
        }


def download_entries(entries, mode, out_dir, ext):
    total = len(entries)
    print(f"\nNombre d’éléments : {total}\n")

    for idx, entry in enumerate(entries, start=1):
        title = entry.get("title", "Sans titre")
        print(f"Téléchargement {idx}/{total} : {title}\n")

        ydl_opts = build_ydl_opts(mode, out_dir, ext)
        entry_url = entry.get("webpage_url") or entry.get("url")

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([entry_url])

            print("✔ Terminé.\n")

        except Exception as e:
            print(f"❌ Erreur : {e}\n")
            continue


# ============================================================
#  PROGRAMME PRINCIPAL
# ============================================================

def main():
    while True:
        choice = main_menu()

        if choice == "3":
            clear()
            print("À bientôt !")
            sys.exit(0)

        elif choice in ["1", "2"]:
            mode = "video" if choice == "1" else "audio"

            save_path = ask_path()

            clear()
            print(f"Mode : {mode.upper()}")
            url = input("\nColle l’URL YouTube : ").strip()

            if not url:
                print("URL vide.")
                time.sleep(1)
                continue

            clear()
            print("Analyse de l’URL...\n")

            try:
                info = analyze_url(url)
            except Exception as e:
                print(f"Impossible d’analyser l’URL : {e}")
                input("\nEntrée pour continuer...")
                continue

            entries = build_entries(info)

            if not entries:
                print("Aucun élément trouvé.")
                input("\nEntrée pour continuer...")
                continue

            ext = choose_format(mode)

            clear()
            print(f"Chemin : {save_path}")
            print(f"Format : {ext}\n")

            download_entries(entries, mode, save_path, ext)

            print("\n✔ Tous les téléchargements sont terminés.")
            print(f"📁 Fichiers enregistrés dans : {save_path}")
            input("\nEntrée pour revenir au menu...")

        else:
            print("Choix invalide.")
            time.sleep(1)


if __name__ == "__main__":
    main()
