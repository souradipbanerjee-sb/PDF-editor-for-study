import tkinter as tk
from tkinter import filedialog, messagebox
import fitz  # PyMuPDF
from PIL import Image, ImageTk, ImageDraw, ImageOps
import os

class PDFEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quick PDF Triage & Study Tool")
        self.root.geometry("1200x950")
        self.root.configure(bg="#1e1e1e")

        # Application State
        self.doc = None
        self.current_page = 0
        self.zoom_level = 1.3
        self.pdf_path = ""
        self.dark_mode = False
        self.starred_pages = set()
        
        # Search state
        self.search_results = []
        self.last_search_term = ""
        self.search_page_iterator = 0

        self.undo_stack = []  
        self.redo_stack = []

        # --- UI LAYOUT ---
        self.top_frame = tk.Frame(self.root, bg="#2e2e2e")
        self.top_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        # 1. Search & Page Navigation
        tk.Label(self.top_frame, text="Search:", bg="#2e2e2e", fg="white").pack(side=tk.LEFT, padx=(10, 2))
        self.search_entry = tk.Entry(self.top_frame, width=15)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search_text())

        tk.Label(self.top_frame, text="Page:", bg="#2e2e2e", fg="white").pack(side=tk.LEFT, padx=(10, 2))
        self.seek_entry = tk.Entry(self.top_frame, width=5)
        self.seek_entry.pack(side=tk.LEFT, padx=5)
        self.seek_entry.bind("<Return>", lambda e: self.jump_to_page())

        # 2. Study Controls
        tk.Button(self.top_frame, text="⭐ Star Page", command=self.toggle_star, bg="#fbc02d", fg="black").pack(side=tk.LEFT, padx=10)
        tk.Button(self.top_frame, text="🌓 Night Mode", command=self.toggle_dark_mode, bg="#444", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(self.top_frame, text="🔄 Rotate", command=self.rotate_page).pack(side=tk.LEFT, padx=5)
        tk.Button(self.top_frame, text="📸 Snap", command=self.snap_page, bg="#2e7d32", fg="white").pack(side=tk.LEFT, padx=5)

        # 3. Main Actions
        tk.Button(self.top_frame, text="Open PDF", command=self.open_pdf).pack(side=tk.LEFT, padx=20)
        tk.Button(self.top_frame, text="Help (?)", command=self.show_instructions, bg="#555", fg="white").pack(side=tk.RIGHT, padx=10)
        tk.Button(self.top_frame, text="Export Digest", command=self.export_digest, bg="#7b1fa2", fg="white").pack(side=tk.RIGHT, padx=5)
        tk.Button(self.top_frame, text="Save PDF", command=self.save_pdf, bg="#1565c0", fg="white").pack(side=tk.RIGHT, padx=5)
        
        self.page_label = tk.Label(self.root, text="No PDF Loaded", bg="#1e1e1e", fg="#888", font=("Arial", 11, "bold"))
        self.page_label.pack(side=tk.TOP, pady=2)

        self.container = tk.Frame(self.root, bg="#1e1e1e")
        self.container.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(self.container, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(expand=True)

        # Keyboard Bindings
        self.root.bind("<Left>", lambda e: self.prev_page())
        self.root.bind("<Right>", lambda e: self.next_page())
        self.root.bind("<Up>", lambda e: self.prev_page())
        self.root.bind("<Down>", lambda e: self.next_page())
        self.root.bind("<Delete>", lambda e: self.delete_page())
        self.root.bind("<Control-s>", lambda e: self.save_pdf())
        self.root.bind("<Control-S>", lambda e: self.save_pdf())
        self.root.bind("<space>", lambda e: self.toggle_star())
        self.root.bind("<Control-z>", lambda e: self.undo_delete())
        self.root.bind("<Control-y>", lambda e: self.redo_delete())
        self.root.bind("<plus>", lambda e: self.zoom_in())
        self.root.bind("<equal>", lambda e: self.zoom_in())
        self.root.bind("<minus>", lambda e: self.zoom_out())

        self.show_instructions()

    def show_instructions(self):
        guide = (
            "🚀 PDF Triage & Study Tool - Master Guide\n\n"
            "📖 NAVIGATION\n"
            "• Arrows: Flip pages | Spacebar: Star/Unstar page\n"
            "• Page Box + Enter: Jump to page | +/-: Zoom\n\n"
            "🔍 SEARCH\n"
            "• Search Bar + Enter: Find text. Press Enter AGAIN to find next instance.\n\n"
            "⭐ STUDY & DIGEST\n"
            "• Export Digest: Save ONLY starred pages as a new PDF.\n"
            "• Night Mode: Toggle dark reading theme.\n"
            "• Snap: Save current view as PNG image.\n\n"
            "🛠 EDITING & SAVING\n"
            "• Delete Key: Remove page | Ctrl+Z/Y: Undo/Redo\n"
            "• Ctrl + S: Save modifications (overwrites original safely).\n"
            "• Rotate: Turn page 90 degrees."
        )
        messagebox.showinfo("User Guide", guide)

    def open_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if path:
            self.pdf_path = path
            self.doc = fitz.open(path)
            self.current_page = 0
            self.starred_pages = set()
            self.show_page()

    def search_text(self):
        term = self.search_entry.get()
        if not self.doc or not term: return

        # Reset search if term changes
        if term != self.last_search_term:
            self.last_search_term = term
            search_start_pg = self.current_page
        else:
            # Continue from the next page
            search_start_pg = self.current_page + 1

        found = False
        for i in range(search_start_pg, len(self.doc)):
            p = self.doc.load_page(i)
            res = p.search_for(term)
            if res:
                self.current_page = i
                self.search_results = res
                self.show_page(highlight=True)
                found = True
                break

        if not found:
            retry = messagebox.askyesno("Search End", f"No more instances of '{term}'. Search from the beginning?")
            if retry:
                for i in range(0, search_start_pg):
                    p = self.doc.load_page(i)
                    res = p.search_for(term)
                    if res:
                        self.current_page = i
                        self.search_results = res
                        self.show_page(highlight=True)
                        found = True
                        break
                if not found:
                    messagebox.showinfo("Search", "Word not found in document.")

    def toggle_star(self):
        if not self.doc: return
        if self.current_page in self.starred_pages:
            self.starred_pages.remove(self.current_page)
        else:
            self.starred_pages.add(self.current_page)
        self.show_page(highlight=len(self.search_results)>0)

    def export_digest(self):
        if not self.starred_pages:
            messagebox.showwarning("Empty", "No pages starred yet!")
            return
        save_path = filedialog.asksaveasfilename(initialfile="Digest.pdf", defaultextension=".pdf")
        if save_path:
            digest = fitz.open()
            for pg in sorted(list(self.starred_pages)):
                digest.insert_pdf(self.doc, from_page=pg, to_page=pg)
            digest.save(save_path)
            digest.close()
            messagebox.showinfo("Success", "Digest exported!")

    def show_page(self, highlight=False):
        if not self.doc or len(self.doc) == 0: return
        page = self.doc.load_page(self.current_page)
        mat = fitz.Matrix(self.zoom_level, self.zoom_level)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        if self.dark_mode: img = ImageOps.invert(img)
        if highlight and self.search_results:
            draw = ImageDraw.Draw(img, "RGBA")
            h_color = (0, 255, 255, 100) if self.dark_mode else (255, 255, 0, 100)
            for rect in self.search_results:
                scaled = [r * self.zoom_level for r in rect]
                draw.rectangle(scaled, fill=h_color, outline="white")
        self.photo = ImageTk.PhotoImage(image=img)
        self.canvas.config(width=pix.width, height=pix.height)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        star_status = " ⭐ STARRED" if self.current_page in self.starred_pages else ""
        self.page_label.config(text=f"Page: {self.current_page + 1} / {len(self.doc)} | Zoom: {int(self.zoom_level*100)}%{star_status}",
                               fg="#fbc02d" if self.current_page in self.starred_pages else "#888")

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.show_page(highlight=len(self.search_results)>0)

    def rotate_page(self):
        if not self.doc: return
        p = self.doc.load_page(self.current_page)
        p.set_rotation((p.rotation + 90) % 360)
        self.show_page()

    def jump_to_page(self):
        try:
            val = int(self.seek_entry.get()) - 1
            if 0 <= val < len(self.doc):
                self.current_page = val
                self.show_page()
            self.seek_entry.delete(0, tk.END)
        except: pass

    def next_page(self):
        if self.doc and self.current_page < len(self.doc) - 1:
            self.current_page += 1
            self.search_results = []
            self.show_page()

    def prev_page(self):
        if self.doc and self.current_page > 0:
            self.current_page -= 1
            self.search_results = []
            self.show_page()

    def zoom_in(self):
        self.zoom_level += 0.1
        self.show_page(highlight=len(self.search_results)>0)

    def zoom_out(self):
        if self.zoom_level > 0.3:
            self.zoom_level -= 0.1
            self.show_page(highlight=len(self.search_results)>0)

    def snap_page(self):
        if not self.doc: return
        page = self.doc.load_page(self.current_page)
        pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_level, self.zoom_level))
        path = filedialog.asksaveasfilename(defaultextension=".png")
        if path: pix.save(path)

    def delete_page(self):
        if not self.doc or len(self.doc) <= 1: return
        temp_doc = fitz.open()
        temp_doc.insert_pdf(self.doc, from_page=self.current_page, to_page=self.current_page)
        self.undo_stack.append((temp_doc, self.current_page))
        if len(self.undo_stack) > 3: self.undo_stack.pop(0)[0].close()
        if self.current_page in self.starred_pages: self.starred_pages.remove(self.current_page)
        self.doc.delete_page(self.current_page)
        if self.current_page >= len(self.doc): self.current_page = len(self.doc)-1
        self.show_page()

    def undo_delete(self):
        if not self.undo_stack: return
        temp, idx = self.undo_stack.pop()
        self.redo_stack.append((temp, idx))
        self.doc.insert_pdf(temp, start_at=idx)
        self.current_page = idx
        self.show_page()

    def redo_delete(self):
        if not self.redo_stack: return
        temp, idx = self.redo_stack.pop()
        self.undo_stack.append((temp, idx))
        self.current_page = idx
        self.doc.delete_page(idx)
        self.show_page()

    def save_pdf(self):
        if not self.doc: return
        save_path = filedialog.asksaveasfilename(initialfile=os.path.basename(self.pdf_path),
                                                 defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if not save_path: return
        try:
            if os.path.abspath(save_path) == os.path.abspath(self.pdf_path):
                temp_p = save_path + ".tmp"
                self.doc.save(temp_p, garbage=4, deflate=True)
                self.doc.close()
                if os.path.exists(save_path): os.remove(save_path)
                os.rename(temp_p, save_path)
                self.doc = fitz.open(save_path)
                messagebox.showinfo("Success", "File Overwritten!")
            else:
                self.doc.save(save_path, garbage=4, deflate=True)
                messagebox.showinfo("Success", "PDF Saved!")
        except Exception as e:
            messagebox.showerror("Error", f"{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFEditorApp(root)
    root.mainloop()