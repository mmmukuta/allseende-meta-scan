# 🛡️ ALLSEENDE META SCAN 

**ALLSEENDE META SCAN** is a professional desktop application designed to analyze, visualize, and securely eradicate hidden metadata (EXIF, GPS, Device Info) from image files. Built with a strict Privacy-First approach.

Every time you share a photo, you might be unintentionally leaking your exact GPS coordinates, camera model, and creation timestamps. ALLSEENDE META SCAN exposes these vulnerabilities and generates a 100% anonymous, clean copy of your file with a single click—without compromising image quality.

##  Key Features
*  **Smart Exposure Scanner:** Filters out technical noise and highlights only critical data markers (Geolocation, Lens Model, Original Timestamps).
*  **Safety Score System:** Automatically evaluates the digital footprint of the file and assigns a security rating (Vulnerable / Secure).
*  **Deep Data Purge:** Completely wipes the digital footprint by rebuilding the image matrix, leaving zero traces behind.
*  **Cyber-UI:** A modern, frameless graphical interface with Drag-and-Drop support, custom rendering, and a dark-mode aesthetic.

##  Tech Stack
* **Core:** Python 3.x
* **GUI:** PyQt5 (Custom QPainter Graphics)
* **EXIF Manipulation:** piexif
* **Image Processing:** Pillow (PIL)

## 🚀 How to Install and Run

1. Clone: `git clone https://github.com/mmmukuta/allseende-meta-scan.git`
2. Install libraries: `python -m pip install -r requirements.txt`
3. Start: `python main.py`
