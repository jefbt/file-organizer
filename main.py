import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import re
from PIL import Image
import threading
from tkinterdnd2 import TkinterDnD, DND_FILES

# --- Theme Configuration ---
GOLD = "#D4AF37"
DARK_GOLD = "#AA8C2C"
BLACK = "#000000"
DARK_GRAY = "#1A1A1A"
TEXT_COLOR = "#FFFFFF"  # White for general text readability against dark gray
GOLD_TEXT = "#D4AF37"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")  # We will override colors manually

class SortableFileList(ctk.CTkScrollableFrame):
    def __init__(self, master, allowed_extensions=None, **kwargs):
        super().__init__(master, **kwargs)
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions] if allowed_extensions else None
        self.file_paths = []
        self.labels = []
        self.drag_source = None
        self.drag_source_index = None
        self.dragging = False

        # Configure drag visuals
        self.drag_highlight_color = "#333333"

        # Register Drop
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self._on_drop)
        
        # Register Drop on internal widgets (Canvas etc) because they cover the main frame
        children_widgets = []
        try:
            if hasattr(self, "_parent_canvas"):
                children_widgets.append(self._parent_canvas)
            if hasattr(self, "_scrollbar"):
                children_widgets.append(self._scrollbar)
        except Exception:
            pass

        for widget in children_widgets:
            try:
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind('<<Drop>>', self._on_drop)
            except Exception as e:
                print(f"Failed to register DND for {widget}: {e}")

    def _is_valid_file(self, path):
        if not os.path.isfile(path):
            return False

        if self.allowed_extensions:
            _, ext = os.path.splitext(path)
            if ext.lower() not in self.allowed_extensions:
                return False

        return True

    def _folder_has_subfolders(self, folder_path):
        try:
            with os.scandir(folder_path) as it:
                for entry in it:
                    if entry.is_dir():
                        return True
        except Exception:
            return False
        return False

    def _ask_folder_drop_mode(self):
        result = {"value": None}
        win = ctk.CTkToplevel(self.winfo_toplevel())
        win.title("What files to add")
        win.resizable(False, False)

        container = ctk.CTkFrame(win, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        lbl = ctk.CTkLabel(container, text="What files to add", text_color=GOLD)
        lbl.pack(pady=(0, 15))

        def choose(val):
            result["value"] = val
            try:
                win.grab_release()
            except Exception:
                pass
            win.destroy()

        btn_folder_only = ctk.CTkButton(container, text="Folder only", command=lambda: choose("folder_only"),
                                        fg_color=GOLD, text_color=BLACK, hover_color=DARK_GOLD)
        btn_folder_only.pack(fill="x", pady=5)

        btn_direct = ctk.CTkButton(container, text="Direct Subfolders", command=lambda: choose("direct_subfolders"),
                                   fg_color=GOLD, text_color=BLACK, hover_color=DARK_GOLD)
        btn_direct.pack(fill="x", pady=5)

        btn_all = ctk.CTkButton(container, text="All children", command=lambda: choose("all_children"),
                                fg_color=GOLD, text_color=BLACK, hover_color=DARK_GOLD)
        btn_all.pack(fill="x", pady=5)

        win.protocol("WM_DELETE_WINDOW", lambda: choose(None))

        try:
            win.transient(self.winfo_toplevel())
            win.grab_set()
        except Exception:
            pass

        self.wait_window(win)
        return result["value"]

    def _iter_folder_files(self, folder_path, mode):
        if mode == "folder_only":
            try:
                with os.scandir(folder_path) as it:
                    for entry in it:
                        if entry.is_file() and self._is_valid_file(entry.path):
                            yield entry.path
            except Exception:
                return
            return

        if mode == "direct_subfolders":
            yield from self._iter_folder_files(folder_path, "folder_only")
            try:
                with os.scandir(folder_path) as it:
                    for entry in it:
                        if entry.is_dir():
                            yield from self._iter_folder_files(entry.path, "folder_only")
            except Exception:
                return
            return

        if mode == "all_children":
            try:
                for root, _, files in os.walk(folder_path):
                    for name in files:
                        p = os.path.join(root, name)
                        if self._is_valid_file(p):
                            yield p
            except Exception:
                return
            return

    def add_path(self, path):
        if os.path.isdir(path):
            mode = "folder_only"
            if self._folder_has_subfolders(path):
                chosen = self._ask_folder_drop_mode()
                if not chosen:
                    return
                mode = chosen

            for file_path in self._iter_folder_files(path, mode):
                self.add_file(file_path)
            return

        self.add_file(path)

    def _on_drop(self, event):
        if event.data:
            try:
                files = self.tk.splitlist(event.data)
                for f in files:
                    self.add_path(f)
            except Exception as e:
                print(f"Drop error: {e}")

    def add_file(self, path):
        if path in self.file_paths:
            return

        if not self._is_valid_file(path):
            return

        self.file_paths.append(path)
        
        # Create a container frame for the label to handle events better or just the label
        # Using CTkLabel directly
        lbl = ctk.CTkLabel(self, text=os.path.basename(path), text_color="white", anchor="w", cursor="hand2")
        lbl.pack(fill="x", padx=5, pady=2)
        
        # Bind events for Drag and Drop (Internal Reorder)
        lbl.bind("<Button-1>", self._on_drag_start)
        lbl.bind("<B1-Motion>", self._on_drag_motion)
        lbl.bind("<ButtonRelease-1>", self._on_drag_stop)
        
        # Register Label as Drop Target for External Files
        # This is CRITICAL because the label covers the frame background
        try:
            lbl.drop_target_register(DND_FILES)
            lbl.dnd_bind('<<Drop>>', self._on_drop)
        except Exception:
            pass # In case widget doesn't support it (though CTkLabel usually wraps a widget that does if root is DnD)

        self.labels.append(lbl)

    def clear(self):
        for lbl in self.labels:
            lbl.destroy()
        self.labels = []
        self.file_paths = []

    def get_files(self):
        return self.file_paths

    def _on_drag_start(self, event):
        self.dragging = True
        self.drag_source = event.widget
        # Find the CTkLabel wrapper if event.widget is the internal tkinter label
        # In CTk, event.widget from bind on CTkLabel is usually the internal tkinter label/canvas.
        # We need to match it to our self.labels list.
        
        # Search for the label object that owns this widget or is this widget
        self.drag_source_item = None
        self.drag_source_index = -1
        
        # CTk specific: event.widget might be the internal widget.
        # We can iterate our labels and check which one matches or contains event.widget
        for i, lbl in enumerate(self.labels):
            if lbl == event.widget or event.widget in lbl.winfo_children() or str(event.widget).startswith(str(lbl)):
                # The str(event.widget).startswith(str(lbl)) check helps if the event comes from a child
                self.drag_source_item = lbl
                self.drag_source_index = i
                break
        
        if self.drag_source_item:
            self.drag_source_item.configure(fg_color=self.drag_highlight_color)

    def _on_drag_motion(self, event):
        if not self.dragging or self.drag_source_item is None:
            return

        y_root = self.winfo_pointery()
        
        # Check which item we are over
        target_index = -1
        for i, lbl in enumerate(self.labels):
            lbl_y = lbl.winfo_rooty()
            lbl_h = lbl.winfo_height()
            # Add some buffer or just check strict bounds
            if lbl_y <= y_root <= lbl_y + lbl_h:
                target_index = i
                break
        
        if target_index != -1 and target_index != self.drag_source_index:
            # Swap logic
            # Move element in lists
            item = self.labels.pop(self.drag_source_index)
            path = self.file_paths.pop(self.drag_source_index)
            
            self.labels.insert(target_index, item)
            self.file_paths.insert(target_index, path)
            
            self.drag_source_index = target_index
            
            # Re-pack everything
            for lbl in self.labels:
                lbl.pack_forget()
            for lbl in self.labels:
                lbl.pack(fill="x", padx=5, pady=2)

    def _on_drag_stop(self, event):
        self.dragging = False
        if self.drag_source_item:
            self.drag_source_item.configure(fg_color="transparent")
        self.drag_source = None
        self.drag_source_item = None

    def repack_items(self):
        for lbl in self.labels:
            lbl.pack_forget()
        for lbl in self.labels:
            lbl.pack(fill="x", padx=5, pady=2)

    def invert_order(self):
        self.file_paths.reverse()
        self.labels.reverse()
        self.repack_items()

    def sort_by_name(self):
        if not self.file_paths: return
        combined = list(zip(self.file_paths, self.labels))
        combined.sort(key=lambda x: os.path.basename(x[0]).lower())
        self.file_paths, self.labels = zip(*combined)
        self.file_paths = list(self.file_paths)
        self.labels = list(self.labels)
        self.repack_items()

    def sort_by_date(self):
        if not self.file_paths: return
        combined = list(zip(self.file_paths, self.labels))
        # Sort by modification time, handling potential missing files
        combined.sort(key=lambda x: os.path.getmtime(x[0]) if os.path.exists(x[0]) else 0)
        self.file_paths, self.labels = zip(*combined)
        self.file_paths = list(self.file_paths)
        self.labels = list(self.labels)
        self.repack_items()

class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("Organizer - Gold Edition")
        self.geometry("900x700")
        self.configure(fg_color=BLACK)

        # Main Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Tab View
        self.tabview = ctk.CTkTabview(self, 
                                      fg_color=DARK_GRAY, 
                                      segmented_button_fg_color=BLACK,
                                      segmented_button_selected_color=GOLD,
                                      segmented_button_selected_hover_color=DARK_GOLD,
                                      segmented_button_unselected_color=DARK_GRAY,
                                      segmented_button_unselected_hover_color="#333333",
                                      text_color=BLACK) # Text color on the selected button (Gold) needs to be black or contrasting. 
        # Actually CTk doesn't allow changing text color for selected vs unselected easily in constructor alone for some versions, 
        # but let's try setting text_color which applies to all. 
        # If the button is Gold, Black text is good. If button is Black, Black text is bad.
        # Let's keep text_color='white' usually, but with Gold background, White might be hard to read.
        # Let's try text_color converted dynamically or just use White and pick a Darker Gold if needed. 
        # Or better: Text Color White, Selected Color Gold.
        
        self.tabview.configure(text_color="white") # Default text color
        
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.tabview.add("Renaming")
        self.tabview.add("Converting")

        # --- Tab 1: Renaming ---
        self.setup_renaming_tab()

        # --- Tab 2: Converting ---
        self.setup_converting_tab()

    def setup_renaming_tab(self):
        tab = self.tabview.tab("Renaming")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1) # File list expands

        # Options Frame
        options_frame = ctk.CTkFrame(tab, fg_color="transparent")
        options_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Start Number Input (Hidden by default, created first to be safe)
        self.rename_start_input = ctk.CTkEntry(options_frame, placeholder_text="Start #", width=60,
                                               border_color=GOLD, fg_color=BLACK, text_color=GOLD)

        # Dropdown
        self.rename_option_var = ctk.StringVar(value="Ordered renaming") # Set as default to test
        self.rename_option_menu = ctk.CTkOptionMenu(options_frame, 
                                                    variable=self.rename_option_var,
                                                    values=[
                                                        "After X characters", 
                                                        "Before X characters", 
                                                        "After expression", 
                                                        "Before expression", 
                                                        "Remove expression only",
                                                        "Ordered renaming"
                                                    ],
                                                    command=self._on_rename_mode_change,
                                                    fg_color=GOLD,
                                                    button_color=DARK_GOLD,
                                                    button_hover_color=GOLD,
                                                    text_color=BLACK,
                                                    dropdown_fg_color=DARK_GRAY,
                                                    dropdown_text_color=GOLD)
        self.rename_option_menu.pack(side="left", padx=5)
        
        # Trigger the mode change manually for the default value
        self.after(100, lambda: self._on_rename_mode_change("Ordered renaming"))

        # Input Entry (for X or Expression)

        # Input Entry (for X or Expression)
        self.rename_input = ctk.CTkEntry(options_frame, placeholder_text="Value (X or Expression)", 
                                         border_color=GOLD, fg_color=BLACK, text_color=GOLD)
        self.rename_input.pack(side="left", padx=5, fill="x", expand=True)

        # Buttons Frame
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.btn_add_rename = ctk.CTkButton(btn_frame, text="Add Files", command=self.add_files_rename,
                                            fg_color=GOLD, text_color=BLACK, hover_color=DARK_GOLD)
        self.btn_add_rename.pack(side="left", padx=5)

        self.btn_clear_rename = ctk.CTkButton(btn_frame, text="Clear List", command=self.clear_list_rename,
                                              fg_color=DARK_GRAY, border_color=GOLD, border_width=2, 
                                              text_color=GOLD, hover_color="#333333")
        self.btn_clear_rename.pack(side="left", padx=5)

        self.btn_run_rename = ctk.CTkButton(btn_frame, text="Apply Rename", command=self.run_rename,
                                            fg_color=GOLD, text_color=BLACK, hover_color=DARK_GOLD)
        self.btn_run_rename.pack(side="right", padx=5)

        self.btn_sort_date_rename = ctk.CTkButton(btn_frame, text="Sort Date", width=80, 
                                              fg_color=DARK_GRAY, border_color=GOLD, border_width=2, 
                                              text_color=GOLD, hover_color="#333333")
        self.btn_sort_date_rename.pack(side="right", padx=5)

        self.btn_sort_name_rename = ctk.CTkButton(btn_frame, text="Sort Name", width=80,
                                              fg_color=DARK_GRAY, border_color=GOLD, border_width=2, 
                                              text_color=GOLD, hover_color="#333333")
        self.btn_sort_name_rename.pack(side="right", padx=5)

        self.btn_invert_rename = ctk.CTkButton(btn_frame, text="Invert", width=60,
                                              fg_color=DARK_GRAY, border_color=GOLD, border_width=2, 
                                              text_color=GOLD, hover_color="#333333")
        self.btn_invert_rename.pack(side="right", padx=5)

        # File List (Scrollable Frame imitating a list)
        self.rename_file_list_frame = SortableFileList(tab, fg_color=BLACK, border_color=GOLD, border_width=1)
        self.rename_file_list_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # Configure commands for sort buttons NOW that list frame exists
        self.btn_sort_date_rename.configure(command=self.rename_file_list_frame.sort_by_date)
        self.btn_sort_name_rename.configure(command=self.rename_file_list_frame.sort_by_name)
        self.btn_invert_rename.configure(command=self.rename_file_list_frame.invert_order)

    def setup_converting_tab(self):
        tab = self.tabview.tab("Converting")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        # Options Frame
        options_frame = ctk.CTkFrame(tab, fg_color="transparent")
        options_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(options_frame, text="Convert images to:", text_color=GOLD).pack(side="left", padx=5)

        self.convert_format_var = ctk.StringVar(value="png")
        self.convert_option_menu = ctk.CTkOptionMenu(options_frame,
                                                     variable=self.convert_format_var,
                                                     values=["png", "jpg", "jpeg", "webp", "bmp", "ico", "tiff"],
                                                     fg_color=GOLD,
                                                     button_color=DARK_GOLD,
                                                     button_hover_color=GOLD,
                                                     text_color=BLACK,
                                                     dropdown_fg_color=DARK_GRAY,
                                                     dropdown_text_color=GOLD)
        self.convert_option_menu.pack(side="left", padx=5)

        self.keep_old_files_var = ctk.BooleanVar(value=True)
        self.check_keep_files = ctk.CTkCheckBox(options_frame, text="Keep old files", variable=self.keep_old_files_var,
                                                fg_color=GOLD, checkmark_color=BLACK, hover_color=DARK_GOLD, text_color=GOLD)
        self.check_keep_files.pack(side="left", padx=20)

        # Buttons Frame
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.btn_add_convert = ctk.CTkButton(btn_frame, text="Add Files", command=self.add_files_convert,
                                             fg_color=GOLD, text_color=BLACK, hover_color=DARK_GOLD)
        self.btn_add_convert.pack(side="left", padx=5)

        self.btn_clear_convert = ctk.CTkButton(btn_frame, text="Clear List", command=self.clear_list_convert,
                                               fg_color=DARK_GRAY, border_color=GOLD, border_width=2, 
                                               text_color=GOLD, hover_color="#333333")
        self.btn_clear_convert.pack(side="left", padx=5)

        self.btn_run_convert = ctk.CTkButton(btn_frame, text="Convert All", command=self.run_convert,
                                             fg_color=GOLD, text_color=BLACK, hover_color=DARK_GOLD)
        self.btn_run_convert.pack(side="right", padx=5)

        self.btn_sort_date_convert = ctk.CTkButton(btn_frame, text="Sort Date", width=80, 
                                              fg_color=DARK_GRAY, border_color=GOLD, border_width=2, 
                                              text_color=GOLD, hover_color="#333333")
        self.btn_sort_date_convert.pack(side="right", padx=5)

        self.btn_sort_name_convert = ctk.CTkButton(btn_frame, text="Sort Name", width=80, 
                                              fg_color=DARK_GRAY, border_color=GOLD, border_width=2, 
                                              text_color=GOLD, hover_color="#333333")
        self.btn_sort_name_convert.pack(side="right", padx=5)

        self.btn_invert_convert = ctk.CTkButton(btn_frame, text="Invert", width=60, 
                                              fg_color=DARK_GRAY, border_color=GOLD, border_width=2, 
                                              text_color=GOLD, hover_color="#333333")
        self.btn_invert_convert.pack(side="right", padx=5)

        # File List
        self.convert_file_list_frame = SortableFileList(tab, allowed_extensions=[".jpg", ".jpeg", ".png", ".webp", ".bmp", ".ico", ".tiff", ".gif"], fg_color=BLACK, border_color=GOLD, border_width=1)
        self.convert_file_list_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # Configure commands for sort buttons NOW that list frame exists
        self.btn_sort_date_convert.configure(command=self.convert_file_list_frame.sort_by_date)
        self.btn_sort_name_convert.configure(command=self.convert_file_list_frame.sort_by_name)
        self.btn_invert_convert.configure(command=self.convert_file_list_frame.invert_order)

    # --- Logic: Renaming ---

    def _on_rename_mode_change(self, choice):
        if choice == "Ordered renaming":
            self.rename_input.pack_forget()
            self.rename_start_input.pack(side="left", padx=5)
            self.rename_input.pack(side="left", padx=5, fill="x", expand=True)
            self.rename_input.configure(placeholder_text="Pattern (e.g. File-@@@@@)")
            if not self.rename_input.get():
                self.rename_input.insert(0, "@@@@@")
            if not self.rename_start_input.get():
                self.rename_start_input.insert(0, "1")
        else:
            self.rename_start_input.pack_forget()
            self.rename_input.configure(placeholder_text="Value (X or Expression)")
            # Clear default pattern if present to avoid confusion? 
            # Or leave it. Let's leave it, user might switch back.

    def add_files_rename(self):
        files = filedialog.askopenfilenames(title="Select files to rename")
        for f in files:
            self.rename_file_list_frame.add_file(f)

    def clear_list_rename(self):
        self.rename_file_list_frame.clear()

    def run_rename(self):
        rename_files = self.rename_file_list_frame.get_files()
        if not rename_files:
            messagebox.showwarning("Warning", "No files selected.")
            return
        
        mode = self.rename_option_var.get()
        value = self.rename_input.get()

        if not value:
            messagebox.showerror("Error", "Please provide a value (X characters or Expression).")
            return

        count = 0
        try:
            for file_path in rename_files:
                directory = os.path.dirname(file_path)
                filename = os.path.basename(file_path)
                name, ext = os.path.splitext(filename)
                
                new_name = name # Default

                if mode == "After X characters":
                    # Remove everything AFTER the Xth character (Keep first X)
                    try:
                        x = int(value)
                        new_name = name[:x]
                    except ValueError:
                        messagebox.showerror("Error", "Value must be an integer for 'X characters'.")
                        return

                elif mode == "Before X characters":
                    # Remove everything BEFORE the Xth character (Keep from X to end)
                    try:
                        x = int(value)
                        new_name = name[x:]
                    except ValueError:
                        messagebox.showerror("Error", "Value must be an integer for 'X characters'.")
                        return

                elif mode == "After expression":
                    # Remove everything after the expression
                    if value in name:
                        idx = name.find(value)
                        # Keep part before expression and the expression itself?
                        # Usually "Remove after X" means X is the boundary.
                        # I will assume we keep the expression.
                        new_name = name[:idx+len(value)] 

                elif mode == "Before expression":
                    # Remove everything before the expression
                    if value in name:
                        idx = name.find(value)
                        new_name = name[idx:] # Keep expression + suffix

                elif mode == "Remove expression only":
                    new_name = name.replace(value, "")

                elif mode == "Ordered renaming":
                    # value is Pattern
                    pattern = value
                    start_num_str = self.rename_start_input.get()
                    try:
                        start_num = int(start_num_str) if start_num_str else 1
                    except ValueError:
                         messagebox.showerror("Error", "Start Number must be an integer.")
                         return

                    current_num = start_num + (count) # count starts at 0 for first file in loop
                    
                    # Regex to find sequences of @
                    # We replace each sequence with the formatted number
                    # But the prompt says "The @ symbol ... means a number filled to that amount of zeros."
                    # Implies we replace the @ block with the number padded to block length.
                    
                    def replace_match(match):
                        length = len(match.group(0))
                        return str(current_num).zfill(length)
                    
                    new_name = re.sub(r'@+', replace_match, pattern)

                if new_name == name:
                    continue

                new_full_name = new_name + ext
                new_path = os.path.join(directory, new_full_name)

                # Handle collision
                if os.path.exists(new_path):
                    # Simple collision handling: append _1
                    base_new = new_name
                    c = 1
                    while os.path.exists(os.path.join(directory, f"{base_new}_{c}{ext}")):
                        c += 1
                    new_path = os.path.join(directory, f"{base_new}_{c}{ext}")
                
                os.rename(file_path, new_path)
                count += 1
            
            messagebox.showinfo("Success", f"Renamed {count} files.")
            self.clear_list_rename()

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    # --- Logic: Converting ---

    def add_files_convert(self):
        files = filedialog.askopenfilenames(title="Select images to convert", 
                                            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.bmp *.ico *.tiff *.gif")])
        for f in files:
            self.convert_file_list_frame.add_file(f)

    def clear_list_convert(self):
        self.convert_file_list_frame.clear()

    def run_convert(self):
        convert_files = self.convert_file_list_frame.get_files()
        if not convert_files:
            messagebox.showwarning("Warning", "No files selected.")
            return

        target_ext = self.convert_format_var.get().lower()
        keep_old = self.keep_old_files_var.get()
        
        # PIL format mapping
        format_map = {
            "jpg": "JPEG",
            "jpeg": "JPEG",
            "png": "PNG",
            "webp": "WEBP",
            "bmp": "BMP",
            "ico": "ICO",
            "tiff": "TIFF"
        }
        pil_format = format_map.get(target_ext, "PNG")

        count = 0
        try:
            for file_path in convert_files:
                directory = os.path.dirname(file_path)
                filename = os.path.basename(file_path)
                name, _ = os.path.splitext(filename)
                
                new_filename = f"{name}.{target_ext}"
                new_path = os.path.join(directory, new_filename)

                try:
                    with Image.open(file_path) as img:
                        # Convert mode if necessary (e.g. RGBA to RGB for JPEG)
                        if pil_format == "JPEG" and img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        
                        img.save(new_path, format=pil_format)
                        count += 1
                    
                    if not keep_old:
                        os.remove(file_path)

                except Exception as img_err:
                    print(f"Failed to convert {filename}: {img_err}")
                    # Continue to next file
            
            messagebox.showinfo("Success", f"Converted {count} images.")
            self.clear_list_convert()

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()
