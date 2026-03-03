#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import platform

# ============================================================
#  AUTO-INSTALLATION DES MODULES MANQUANTS
# ============================================================

REQUIRED_MODULES = ["yt_dlp", "ffmpeg"]

def install_missing_modules():
    print("\nModules manquants détectés. Installation en cours...\n")
    subprocess.call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
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
#  CONFIG
# ============================================================

VIDEO_FORMATS = [
    ("mp4", "MP4"),
    ("mkv", "Matroska"),
    ("webm", "WebM"),
    ("avi", "AVI"),
    ("mov", "QuickTime"),
    ("flv", "FLV"),
    ("mpeg", "MPEG"),
    ("3gp", "3GP"),
]

AUDIO_FORMATS = [
    ("mp3", "MP3"),
    ("m4a", "M4A"),
    ("opus", "Opus"),
    ("flac", "FLAC"),
    ("wav", "WAV"),
    ("ogg", "Ogg Vorbis"),
    ("aac", "AAC"),
]

# ============================================================
#  UTILITAIRES
# ============================================================

def clear():
    os.system("cls")


def get_default_path():
    """Chemin par défaut Windows → dossier Vidéos."""
    videos_dir = os.path.join(os.path.expanduser("~"), "Videos")
    return os.path.join(videos_dir, "Youtube_Downloads")


def ask_path(default_path):
    print("\nOù veux‑tu enregistrer les fichiers ?\n")
    print("Chemin (appuie sur ENTRÉE pour utiliser le chemin par défaut) :")
    print(default_path)
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
        print("Choisis le format VIDÉO de sortie :\n")
        formats = VIDEO_FORMATS
    else:
        print("Choisis le format AUDIO de sortie :\n")
        formats = AUDIO_FORMATS

    for i, (ext, label) in enumerate(formats, start=1):
        print(f"{i} - {ext} ({label})")

    while True:
        choice = input("\nChoix : ").strip()
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(formats):
                return formats[idx - 1][0]
        print("Choix invalide, réessaie.")


def choose_channel_mode():
    clear()
    print("URL détectée comme une CHAÎNE YouTube.\n")
    print("Que veux‑tu télécharger ?\n")
    print("1 - Uniquement les VIDÉOS")
    print("2 - Uniquement les SHORTS")
    print("3 - VIDÉOS + SHORTS\n")

    while True:
        choice = input("Choix : ").strip()
        if choice in ["1", "2", "3"]:
            return choice
        print("Choix invalide, réessaie.")


def is_short(entry):
    url = entry.get("webpage_url", "") or entry.get("url", "")
    duration = entry.get("duration")
    if "shorts" in url:
        return True
    if duration is not None and duration <= 60:
        return True
    return False


# ============================================================
#  ANALYSE URL & LISTE DES ENTRÉES
# ============================================================

def analyze_url(url):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "ignoreerrors": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def build_entries_from_info(info, channel_mode=None):
    if info.get("_type") is None:
        return [info]

    entries = info.get("entries") or []
    result = []

    if info.get("_type") == "playlist":
        extractor = info.get("extractor", "")
        if "channel" not in extractor and "user" not in extractor and channel_mode is None:
            return [e for e in entries if e]

    if channel_mode is None:
        return [e for e in entries if e]

    for e in entries:
        if not e:
            continue
        short = is_short(e)
        if channel_mode == "1" and not short:
            result.append(e)
        elif channel_mode == "2" and short:
            result.append(e)
        elif channel_mode == "3":
            result.append(e)

    return result


# ============================================================
#  TÉLÉCHARGEMENT + FFMPEG DIRECT
# ============================================================

def build_ydl_opts(mode, out_dir, ext):
    base_outtmpl = os.path.join(out_dir, "%(title)s.%(ext)s")

    if mode == "video":
        return {
            "outtmpl": base_outtmpl,
            "format": "bestvideo+bestaudio/best",
            "ignoreerrors": True,
            "noplaylist": True,
            "verbose": True,  # ffmpeg visible
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
            "noplaylist": True,
            "verbose": True,  # ffmpeg visible
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
    print(f"\nNombre d’éléments à télécharger : {total}\n")

    for idx, entry in enumerate(entries, start=1):
        title = entry.get("title", "Sans titre")
        print(f"Téléchargement {idx}/{total} : {title}\n")

        ydl_opts = build_ydl_opts(mode, out_dir, ext)
        entry_url = entry.get("webpage_url") or entry.get("url")

        try:
            print("Téléchargement et conversion en cours (ffmpeg affiché ci‑dessous)...\n")
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([entry_url])

            print("\nConversion terminée.")
            print("Téléchargement terminé.\n")

        except Exception as e:
            print(f"\nErreur pendant le téléchargement : {e}\n")
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

            default_path = get_default_path()
            save_path = ask_path(default_path)

            clear()
            print(f"Mode sélectionné : {mode.upper()}")
            url = input("\nColle l’URL YouTube : ").strip()

            if not url:
                print("URL vide, retour au menu...")
                time.sleep(1)
                continue

            clear()
            print("Analyse de l’URL...\n")

            try:
                info = analyze_url(url)
            except Exception as e:
                print(f"Impossible d’analyser l’URL : {e}")
                input("\nAppuie sur Entrée pour revenir au menu...")
                continue

            info_type = info.get("_type")
            channel_mode = None

            if info_type is None:
                print("Type détecté : vidéo unique\n")
            elif info_type == "playlist":
                extractor = info.get("extractor", "")
                if "channel" in extractor or "user" in extractor:
                    channel_mode = choose_channel_mode()
                    print("\nConstruction de la liste des vidéos de la chaîne...\n")
                else:
                    print("Type détecté : playlist\n")
            else:
                print(f"Type détecté : {info_type}\n")

            entries = build_entries_from_info(info, channel_mode=channel_mode)

            if not entries:
                print("Aucun élément à télécharger.")
                input("\nAppuie sur Entrée pour revenir au menu...")
                continue

            ext = choose_format(mode)

            clear()
            print(f"Chemin de téléchargement : {save_path}")
            print(f"Mode : {mode.upper()} | Format : {ext}\n")

            download_entries(entries, mode, save_path, ext)

            print("\nTéléchargements terminés.")
            print(f"\nFichiers enregistrés dans :\n{save_path}")
            input("\nAppuie sur Entrée pour revenir au menu...")

        else:
            print("\nChoix invalide.")
            time.sleep(1)


if __name__ == "__main__":
    main()
