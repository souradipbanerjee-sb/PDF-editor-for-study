# Quick PDF Triage & Study Tool 📚⚡

A lightweight, offline-first Python application designed to streamline the reading and auditing of massive documents, such as MBA case studies, annual reports, and course slide decks.

## ⚠️ The Problem
In fast-paced academic and professional environments, users often deal with 50+ page PDFs where only 10% of the content is critical. Standard viewers are too slow for "triaging" (deleting fluff, starring exhibits, and capturing data).

## ✨ Key Features
- **Study Digest:** Star high-value pages (Spacebar) and export them into a condensed PDF summary.
- **Global Search:** "Find Next" functionality to zip through documents for specific keywords.
- **Night Mode:** Inverted color rendering to reduce eye strain during late-night sessions.
- **Triage Editing:** Instant page deletion, 90° rotation, and undo/redo capabilities.
- **Visual Snap:** Capture charts or tables directly to PNG for use in presentations.
- **Privacy First:** 100% offline. No data leaves your machine—critical for sensitive corporate data.

## 🛠 Tech Stack
- **Python 3.10+**
- **PyMuPDF (fitz):** High-performance PDF manipulation and rendering.
- **Pillow (PIL):** Image processing for Night Mode and snapshots.
- **Tkinter:** Lightweight GUI for cross-platform portability.

## 🚀 How to Run (Source)
1. Clone the repo:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)

2.  Install dependencies:
	pip install pymupdf pillow

3. Launch
	python pdf_for_study.py


# Building the Windows Executable (.exe)
To create a standalone portable version for Windows, follow these steps:

1. Install PyInstaller:
	pip install pyinstaller

2. Run the build command (ensure you are in the project directory):
		pyinstaller --noconsole --onefile --clean ^
		--collect-submodules PIL ^
		--collect-submodules fitz ^
		pdf_for_study.py

3. The standalone file will be generated in the dist/ folder as pdf_triage.exe.
