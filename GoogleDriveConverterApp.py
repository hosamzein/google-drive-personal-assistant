import os
import sys
import time
import shutil
import sqlite3
import webbrowser
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

# Reconfigure stdout for UTF-8 support if run in terminal
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

class TextRedirector(object):
    """Redirects stdout to a tkinter ScrolledText widget."""
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, string):
        self.widget.configure(state='normal')
        self.widget.insert(tk.END, string, self.tag)
        self.widget.see(tk.END)
        self.widget.configure(state='disabled')
        sys.__stdout__.write(string)
        sys.__stdout__.flush()

    def flush(self):
        sys.__stdout__.flush()

class GoogleDriveConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Google Drive Shortcut Converter & Backup Tool")
        self.geometry("780x680")
        self.minsize(700, 550)
        
        # Configure modern dark theme colors
        self.bg_color = "#1e1e1e"
        self.fg_color = "#ffffff"
        self.accent_color = "#007acc"
        self.card_bg = "#2d2d2d"
        self.text_bg = "#121212"
        self.btn_active_bg = "#005999"
        
        self.configure(bg=self.bg_color)
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.option_add("*Font", "SegoeUi 10")
        
        # Ttk widget styling
        self.style.configure(".", background=self.bg_color, foreground=self.fg_color)
        self.style.configure("TLabel", background=self.bg_color, foreground=self.fg_color)
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TCheckbutton", background=self.bg_color, foreground=self.fg_color)
        self.style.map("TCheckbutton", background=[('active', self.bg_color)], foreground=[('active', self.fg_color)])
        
        # Variables
        self.target_dir_var = tk.StringVar()
        self.backup_dir_var = tk.StringVar()
        self.enable_backup_var = tk.BooleanVar(value=False)
        self.dry_run_var = tk.BooleanVar(value=False)
        self.delete_sources_var = tk.BooleanVar(value=False)
        self.is_running = False
        
        # Build UI
        self.create_widgets()
        
        # Redirect standard output and error to our GUI text area
        sys.stdout = TextRedirector(self.log_area, "stdout")
        sys.stderr = TextRedirector(self.log_area, "stderr")

    def create_widgets(self):
        # 1. Title Header
        header_frame = tk.Frame(self, bg=self.card_bg, height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(
            header_frame, 
            text="Google Workspace Converter & Backup", 
            font=("Segoe UI", 13, "bold"), 
            bg=self.card_bg, 
            fg=self.accent_color
        )
        header_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        subtitle_label = tk.Label(
            header_frame, 
            text="Convert .gdoc / .gsheet -> .docx / .xlsx with full directory backup options", 
            font=("Segoe UI", 9, "italic"), 
            bg=self.card_bg, 
            fg="#aaaaaa"
        )
        subtitle_label.pack(side=tk.LEFT, padx=10, pady=18)

        # Main Layout Container
        main_frame = tk.Frame(self, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # 2. Source Folder Selection Section
        folder_frame = tk.Frame(main_frame, bg=self.bg_color)
        folder_frame.pack(fill=tk.X, pady=(0, 8))
        
        folder_label = tk.Label(folder_frame, text="Select Source Folder (Google Drive):", font=("Segoe UI", 10, "bold"), bg=self.bg_color, fg=self.fg_color)
        folder_label.pack(anchor=tk.W, pady=(0, 4))
        
        self.folder_entry = tk.Entry(
            folder_frame, 
            textvariable=self.target_dir_var, 
            bg=self.card_bg, 
            fg=self.fg_color, 
            insertbackground=self.fg_color,
            relief=tk.FLAT, 
            font=("Segoe UI", 10),
            highlightthickness=1,
            highlightbackground="#444444",
            highlightcolor=self.accent_color
        )
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(0, 10))
        
        browse_btn = tk.Button(
            folder_frame, 
            text="Browse...", 
            command=self.browse_folder, 
            bg=self.accent_color, 
            fg=self.fg_color, 
            activebackground=self.btn_active_bg,
            activeforeground=self.fg_color,
            relief=tk.FLAT,
            font=("Segoe UI", 9, "bold"),
            padx=15
        )
        browse_btn.pack(side=tk.RIGHT, ipady=2)

        # 3. Backup Folder Selection Section
        backup_card = tk.Frame(main_frame, bg=self.bg_color)
        backup_card.pack(fill=tk.X, pady=8)
        
        self.backup_cb = ttk.Checkbutton(
            backup_card, 
            text="Backup source directory before starting conversion", 
            variable=self.enable_backup_var,
            command=self.toggle_backup_state
        )
        self.backup_cb.pack(anchor=tk.W, pady=(0, 4))
        
        self.backup_subframe = tk.Frame(backup_card, bg=self.bg_color)
        self.backup_subframe.pack(fill=tk.X, pady=(2, 0))
        
        self.backup_entry = tk.Entry(
            self.backup_subframe, 
            textvariable=self.backup_dir_var, 
            bg=self.card_bg, 
            fg=self.fg_color, 
            insertbackground=self.fg_color,
            relief=tk.FLAT, 
            font=("Segoe UI", 10),
            highlightthickness=1,
            highlightbackground="#444444",
            highlightcolor=self.accent_color,
            state="disabled"
        )
        self.backup_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(0, 10))
        
        self.backup_browse_btn = tk.Button(
            self.backup_subframe, 
            text="Browse...", 
            command=self.browse_backup, 
            bg=self.accent_color, 
            fg=self.fg_color, 
            activebackground=self.btn_active_bg,
            activeforeground=self.fg_color,
            relief=tk.FLAT,
            font=("Segoe UI", 9, "bold"),
            padx=15,
            state="disabled"
        )
        self.backup_browse_btn.pack(side=tk.RIGHT, ipady=2)

        # 4. Settings Options Frame
        settings_frame = tk.Frame(main_frame, bg=self.bg_color)
        settings_frame.pack(fill=tk.X, pady=8)
        
        self.dry_run_cb = ttk.Checkbutton(settings_frame, text="Dry-Run Only (Validate paths and database matches without executing downloads)", variable=self.dry_run_var)
        self.dry_run_cb.pack(anchor=tk.W, pady=3)
        
        self.delete_sources_cb = ttk.Checkbutton(settings_frame, text="Safely Delete Source Shortcuts (.gdoc/.gsheet) after verification", variable=self.delete_sources_var)
        self.delete_sources_cb.pack(anchor=tk.W, pady=3)

        # 5. Action Button
        self.action_btn = tk.Button(
            main_frame, 
            text="Start Backup & Conversion Process", 
            command=self.start_conversion, 
            bg=self.accent_color, 
            fg=self.fg_color, 
            activebackground=self.btn_active_bg,
            activeforeground=self.fg_color,
            relief=tk.FLAT,
            font=("Segoe UI", 11, "bold"),
            pady=8
        )
        self.action_btn.pack(fill=tk.X, pady=10)

        # 6. Log Console Section
        log_label = tk.Label(main_frame, text="Real-Time Operation Status Logs:", font=("Segoe UI", 10, "bold"), bg=self.bg_color, fg=self.fg_color)
        log_label.pack(anchor=tk.W, pady=(5, 5))
        
        self.log_area = ScrolledText(
            main_frame, 
            bg=self.text_bg, 
            fg="#00ff00", 
            insertbackground="#00ff00",
            relief=tk.FLAT, 
            font=("Consolas", 9),
            state='disabled'
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def toggle_backup_state(self):
        # Enable or disable backup inputs based on checkbox
        if self.enable_backup_var.get():
            self.backup_entry.configure(state="normal", highlightbackground="#444444")
            self.backup_browse_btn.configure(state="normal", bg=self.accent_color)
        else:
            self.backup_entry.configure(state="disabled", highlightbackground="#222222")
            self.backup_browse_btn.configure(state="disabled", bg="#555555")

    def browse_folder(self):
        selected = filedialog.askdirectory(title="Select Google Drive Source Folder")
        if selected:
            self.target_dir_var.set(os.path.normpath(selected))

    def browse_backup(self):
        selected = filedialog.askdirectory(title="Select Backup Destination Folder")
        if selected:
            self.backup_dir_var.set(os.path.normpath(selected))

    def start_conversion(self):
        if self.is_running:
            return
            
        target_dir = self.target_dir_var.get().strip()
        if not target_dir:
            messagebox.showerror("Error", "Please select a valid target source folder to work on.")
            return
        if not os.path.exists(target_dir):
            messagebox.showerror("Error", "The specified source folder does not exist.")
            return
            
        # Validate backup fields if enabled
        enable_backup = self.enable_backup_var.get()
        backup_dir = self.backup_dir_var.get().strip()
        if enable_backup:
            if not backup_dir:
                messagebox.showerror("Error", "Please select a valid backup destination directory.")
                return
            if not os.path.exists(backup_dir):
                messagebox.showerror("Error", "The specified backup destination directory does not exist.")
                return
            if os.path.normpath(target_dir) == os.path.normpath(backup_dir):
                messagebox.showerror("Error", "Source folder and Backup folder cannot be the same directory.")
                return

        self.is_running = True
        self.action_btn.configure(state='disabled', bg="#555555", text="Processing Operations...")
        
        # Clear log area
        self.log_area.configure(state='normal')
        self.log_area.delete('1.0', tk.END)
        self.log_area.configure(state='disabled')
        
        # Run conversion and backup in a background thread
        t = threading.Thread(target=self.run_engine, args=(target_dir, enable_backup, backup_dir))
        t.daemon = True
        t.start()

    def run_engine(self, target_dir, enable_backup, backup_dir):
        try:
            dry_run = self.dry_run_var.get()
            delete_sources = self.delete_sources_var.get()
            
            # 1. Execute Backup first if requested
            if enable_backup and not dry_run:
                self.execute_backup(target_dir, backup_dir)
                
            # 2. Execute Conversion
            self.execute_conversion(target_dir, dry_run, delete_sources)
            
        except Exception as e:
            print(f"\n[CRITICAL ERROR] Application crashed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_running = False
            self.action_btn.configure(state='normal', bg=self.accent_color, text="Start Backup & Conversion Process")
            messagebox.showinfo("Completed", "Operations completed. Please check console logs for details.")

    # ------------------ BACKUP LOGIC ENGINE ------------------
    def execute_backup(self, src, dst):
        # Create a timestamped root folder inside backup destination to prevent overwrites
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        folder_name = f"Backup_{os.path.basename(src)}_{timestamp}"
        full_dest_root = os.path.join(dst, folder_name)
        
        print("=" * 60)
        print("STARTING SYSTEM DIRECTORY BACKUP")
        print(f"Source Folder: {src}")
        print(f"Backup Destination: {full_dest_root}")
        print("=" * 60)
        
        # Count total files recursively for progress logging
        total_files = 0
        for r_dir, ds, fs in os.walk(src):
            total_files += len(fs)
            
        print(f"Total source files to backup: {total_files}")
        
        copied_count = 0
        error_count = 0
        
        for r_dir, ds, fs in os.walk(src):
            # Create corresponding subdirectories
            rel_path = os.path.relpath(r_dir, src)
            dest_dir = full_dest_root if rel_path == "." else os.path.join(full_dest_root, rel_path)
            os.makedirs(dest_dir, exist_ok=True)
            
            for f in fs:
                src_file = os.path.join(r_dir, f)
                dest_file = os.path.join(dest_dir, f)
                
                copied_count += 1
                print(f"[{copied_count}/{total_files}] [Backup] Copying: {repr(f)}...")
                
                try:
                    # shutil.copy2 copies file content and metadata (timestamps)
                    shutil.copy2(src_file, dest_file)
                    
                    # Restore Windows creation date
                    stat = os.stat(src_file)
                    self.set_windows_creation_time(dest_file, stat.st_ctime)
                except Exception as e:
                    print(f"Error copying {repr(f)}: {e}")
                    error_count += 1
                    
        print("\n" + "=" * 60)
        print("BACKUP OPERATIONS COMPLETED")
        print(f"Successfully copied: {copied_count - error_count}/{total_files} files")
        if error_count > 0:
            print(f"Errors encountered: {error_count} files failed to copy")
        print("=" * 60 + "\n")

    # ------------------ ENGINE CONVERSION PIPELINE ------------------
    def get_downloads_folder(self):
        return os.path.expandvars(r'%USERPROFILE%\Downloads')

    def get_database_path(self):
        local_app_data = os.environ.get('LOCALAPPDATA', r'C:\Users\PC2\AppData\Local')
        drive_fs_path = os.path.join(local_app_data, 'Google', 'DriveFS')
        if not os.path.exists(drive_fs_path):
            raise FileNotFoundError(f"Google DriveFS path not found: {drive_fs_path}")
            
        for item in os.listdir(drive_fs_path):
            item_path = os.path.join(drive_fs_path, item)
            if os.path.isdir(item_path) and item.isdigit():
                db_path = os.path.join(item_path, 'metadata_sqlite_db')
                if os.path.exists(db_path):
                    return db_path
                    
        raise FileNotFoundError("Could not locate metadata_sqlite_db inside Google DriveFS directory.")

    def load_google_drive_db(self, db_path):
        temp_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metadata_gui_temp.db")
        if os.path.exists(temp_db):
            try:
                os.remove(temp_db)
            except Exception:
                pass
                
        shutil.copyfile(db_path, temp_db)
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT stable_id, id, local_title, mime_type, is_folder FROM items;")
        items_dict = {row[0]: {"id": row[1], "title": row[2], "mime": row[3], "is_folder": row[4]} for row in cursor.fetchall()}
        
        cursor.execute("SELECT item_stable_id, parent_stable_id FROM stable_parents;")
        parents_dict = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        try:
            os.remove(temp_db)
        except Exception:
            pass
            
        return items_dict, parents_dict

    def get_path_parts(self, stable_id, items_dict, parents_dict):
        parts = []
        curr_id = stable_id
        visited = set()
        while curr_id in parents_dict and curr_id not in visited:
            visited.add(curr_id)
            item = items_dict.get(curr_id)
            if not item:
                break
            if item['title'] not in ['My Drive', 'My Laptop', 'Other computers']:
                parts.insert(0, item['title'].lower())
            curr_id = parents_dict[curr_id]
        return parts

    def set_windows_creation_time(self, file_path, creation_time):
        try:
            formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(creation_time))
            ps_cmd = f'powershell -Command "(Get-Item \'{file_path}\').CreationTime = \'{formatted_time}\'"'
            subprocess.run(ps_cmd, shell=True, capture_output=True)
            return True
        except Exception:
            return False

    def execute_conversion(self, target_dir, dry_run, delete_sources):
        print("=" * 60)
        print("STARTING GOOGLE SHORTCUTS CONVERSION ENGINE")
        print(f"Target Directory: {target_dir}")
        print(f"Dry-Run Mode: {dry_run}")
        print(f"Safe Deletion: {delete_sources}")
        print("=" * 60)
        
        # 1. Load Database
        db_path = self.get_database_path()
        print(f"Detecting local Google database: {db_path}")
        items_dict, parents_dict = self.load_google_drive_db(db_path)
        print("Google database successfully loaded.")
        
        # 2. Scan Directory
        print("\nScanning directory recursively for Google shortcuts...")
        google_files = []
        for r_dir, ds, fs in os.walk(target_dir):
            for f in fs:
                ext = os.path.splitext(f)[1].lower()
                if ext in ['.gdoc', '.gsheet']:
                    google_files.append(os.path.normpath(os.path.join(r_dir, f)))
                    
        total_files = len(google_files)
        print(f"Found {total_files} Google shortcut files.")
        if total_files == 0:
            print("\nNo shortcut files to convert. Done.")
            return
            
        downloads_dir = self.get_downloads_folder()
        success_count = 0
        skipped_count = 0
        failed_count = 0
        deleted_count = 0
        
        for idx, local_path in enumerate(google_files, 1):
            filename = os.path.basename(local_path)
            print(f"\n[{idx}/{total_files}] Processing: {repr(filename)}")
            
            base_name = os.path.splitext(filename)[0]
            ext = os.path.splitext(filename)[1].lower()
            
            if ext == '.gdoc':
                target_ext = '.docx'
                mime_filter = 'application/vnd.google-apps.document'
            elif ext == '.gsheet':
                target_ext = '.xlsx'
                mime_filter = 'application/vnd.google-apps.spreadsheet'
            else:
                print("Skipped: Unsupported file format.")
                failed_count += 1
                continue
                
            target_path = os.path.join(os.path.dirname(local_path), base_name + target_ext)
            
            # Check skip condition
            if os.path.exists(target_path):
                print(f"Converted copy already exists: {repr(target_path)}")
                skipped_count += 1
                
                # Safe deletion if requested
                if delete_sources and not dry_run:
                    if os.path.getsize(target_path) > 0:
                        try:
                            os.remove(local_path)
                            print("Original shortcut safely deleted.")
                            deleted_count += 1
                        except Exception as e:
                            print(f"Failed to delete original shortcut: {e}")
                continue
                
            # Path matching in DB
            folder_parts = [p.lower() for p in os.path.relpath(local_path, target_dir).split(os.sep)[:-1]]
            matched_item = None
            filename_lower = filename.lower()
            
            for stable_id, item in items_dict.items():
                if item['title'] and item['title'].lower() == filename_lower and item['mime'] == mime_filter:
                    db_parts = self.get_path_parts(stable_id, items_dict, parents_dict)
                    is_match = True
                    for part in folder_parts:
                        if part not in db_parts:
                            is_match = False
                            break
                    if is_match:
                        matched_item = item
                        break
                        
            if not matched_item:
                print("Warning: Could not match shortcut in Google database.")
                failed_count += 1
                continue
                
            drive_id = matched_item['id']
            print(f"Resolved cloud ID: {drive_id}")
            
            if dry_run:
                print(f"[Dry-Run] Target: {target_path}")
                success_count += 1
                continue
                
            # Record original timestamps
            stat = os.stat(local_path)
            orig_atime = stat.st_atime
            orig_mtime = stat.st_mtime
            orig_ctime = stat.st_ctime
            
            # Build URL
            if ext == '.gdoc':
                export_url = f"https://docs.google.com/document/d/{drive_id}/export?format=docx"
            else:
                export_url = f"https://docs.google.com/spreadsheets/d/{drive_id}/export?format=xlsx"
                
            existing_files = set(os.listdir(downloads_dir))
            print("Opening default browser to download...")
            webbrowser.open(export_url)
            
            # Wait for file download (max 45 seconds)
            start_time = time.time()
            downloaded_file = None
            
            while time.time() - start_time < 45:
                time.sleep(1)
                current_files = set(os.listdir(downloads_dir))
                new_files = current_files - existing_files
                
                for nf in new_files:
                    nf_lower = nf.lower()
                    normalized_nf = nf_lower.replace('_', ' ').replace('-', ' ').strip()
                    normalized_expected = base_name.lower().replace('_', ' ').replace('-', ' ').strip()
                    
                    if nf_lower == (base_name + target_ext).lower():
                        downloaded_file = os.path.join(downloads_dir, nf)
                        break
                    elif normalized_nf.startswith(normalized_expected) and nf_lower.endswith(target_ext):
                        downloaded_file = os.path.join(downloads_dir, nf)
                        break
                        
            if downloaded_file:
                print(f"Download detected: {repr(os.path.basename(downloaded_file))}")
                time.sleep(1.5) # Wait for file lock release
                
                try:
                    shutil.copyfile(downloaded_file, target_path)
                    print(f"Saved: {target_path}")
                    
                    # Restore timestamps
                    os.utime(target_path, (orig_atime, orig_mtime))
                    self.set_windows_creation_time(target_path, orig_ctime)
                    print("Restored original metadata created & modified timestamps.")
                    
                    # Clean up downloads folder
                    try:
                        os.remove(downloaded_file)
                    except Exception:
                        pass
                        
                    success_count += 1
                    
                    # Delete original shortcut if safe deletion is on
                    if delete_sources:
                        try:
                            os.remove(local_path)
                            print("Original shortcut safely deleted.")
                            deleted_count += 1
                        except Exception as e:
                            print(f"Failed to delete original shortcut: {e}")
                            
                except Exception as copy_err:
                    print(f"Error copying/saving file: {copy_err}")
                    failed_count += 1
            else:
                print("Error: Download timed out or failed to start.")
                failed_count += 1
                
        print("\n" + "=" * 60)
        print("CONVERSION ENGINE SUMMARY")
        print(f"Successful conversions: {success_count}")
        print(f"Already converted (skipped): {skipped_count}")
        print(f"Safely deleted shortcuts: {deleted_count}")
        print(f"Failed / Unmatched: {failed_count}")
        print("=" * 60)

if __name__ == '__main__':
    app = GoogleDriveConverterApp()
    app.mainloop()
