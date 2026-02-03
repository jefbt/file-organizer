import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from PIL import Image
import threading

# --- Theme Configuration ---
GOLD = "#D4AF37"
DARK_GOLD = "#AA8C2C"
BLACK = "#000000"
DARK_GRAY = "#1A1A1A"
TEXT_COLOR = "#FFFFFF"  # White for general text readability against dark gray
GOLD_TEXT = "#D4AF37"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")  # We will override colors manually

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

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

        # Dropdown
        self.rename_option_var = ctk.StringVar(value="After X characters")
        self.rename_option_menu = ctk.CTkOptionMenu(options_frame, 
                                                    variable=self.rename_option_var,
                                                    values=[
                                                        "After X characters", 
                                                        "Before X characters", 
                                                        "After expression", 
                                                        "Before expression", 
                                                        "Remove expression only"
                                                    ],
                                                    fg_color=GOLD,
                                                    button_color=DARK_GOLD,
                                                    button_hover_color=GOLD,
                                                    text_color=BLACK,
                                                    dropdown_fg_color=DARK_GRAY,
                                                    dropdown_text_color=GOLD)
        self.rename_option_menu.pack(side="left", padx=5)

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

        # File List (Scrollable Frame imitating a list)
        self.rename_file_list_frame = ctk.CTkScrollableFrame(tab, fg_color=BLACK, border_color=GOLD, border_width=1, label_text="Files to Rename", label_text_color=GOLD)
        self.rename_file_list_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        self.rename_files = [] # List of paths
        self.rename_file_labels = []

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

        # File List
        self.convert_file_list_frame = ctk.CTkScrollableFrame(tab, fg_color=BLACK, border_color=GOLD, border_width=1, label_text="Files to Convert", label_text_color=GOLD)
        self.convert_file_list_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        self.convert_files = []
        self.convert_file_labels = []

    # --- Logic: Renaming ---

    def add_files_rename(self):
        files = filedialog.askopenfilenames(title="Select files to rename")
        for f in files:
            if f not in self.rename_files:
                self.rename_files.append(f)
                lbl = ctk.CTkLabel(self.rename_file_list_frame, text=os.path.basename(f), text_color="white", anchor="w")
                lbl.pack(fill="x", padx=5, pady=2)
                self.rename_file_labels.append(lbl)

    def clear_list_rename(self):
        self.rename_files = []
        for lbl in self.rename_file_labels:
            lbl.destroy()
        self.rename_file_labels = []

    def run_rename(self):
        if not self.rename_files:
            messagebox.showwarning("Warning", "No files selected.")
            return
        
        mode = self.rename_option_var.get()
        value = self.rename_input.get()

        if not value:
            messagebox.showerror("Error", "Please provide a value (X characters or Expression).")
            return

        count = 0
        try:
            for file_path in self.rename_files:
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
            if f not in self.convert_files:
                self.convert_files.append(f)
                lbl = ctk.CTkLabel(self.convert_file_list_frame, text=os.path.basename(f), text_color="white", anchor="w")
                lbl.pack(fill="x", padx=5, pady=2)
                self.convert_file_labels.append(lbl)

    def clear_list_convert(self):
        self.convert_files = []
        for lbl in self.convert_file_labels:
            lbl.destroy()
        self.convert_file_labels = []

    def run_convert(self):
        if not self.convert_files:
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
            for file_path in self.convert_files:
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
