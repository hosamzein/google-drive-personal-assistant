import os
import sys
import time
import shutil
import sqlite3
import webbrowser
import subprocess
import argparse

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def get_downloads_folder():
    return os.path.expandvars(r'%USERPROFILE%\Downloads')

def get_database_path():
    # Detect the numeric Account ID under AppData\Local\Google\DriveFS
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

def load_google_drive_db(db_path):
    temp_db = r"d:\projects\test2\metadata_temp_run.db"
    if os.path.exists(temp_db):
        try:
            os.remove(temp_db)
        except Exception:
            pass
            
    shutil.copyfile(db_path, temp_db)
    
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # Load items and parents
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

def get_path_parts(stable_id, items_dict, parents_dict):
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

def set_windows_creation_time(file_path, creation_time):
    try:
        formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(creation_time))
        # Use PowerShell to set the creation time
        ps_cmd = f'powershell -Command "(Get-Item \'{file_path}\').CreationTime = \'{formatted_time}\'"'
        subprocess.run(ps_cmd, shell=True, capture_output=True)
        return True
    except Exception as e:
        print(f"Error setting creation time: {e}")
        return False

def convert_files(root_dir, dry_run=False):
    print("=" * 60)
    print("GOOGLE DOCS & SHEETS CONVERSION UTILITY")
    print(f"Source Root: {root_dir}")
    print(f"Dry Run Mode: {dry_run}")
    print("=" * 60)
    
    # 1. Load Google Drive metadata database
    try:
        db_path = get_database_path()
        print(f"Found Google Drive database: {db_path}")
        items_dict, parents_dict = load_google_drive_db(db_path)
        print("Database loaded successfully.")
    except Exception as e:
        print(f"Failed to load Google Drive database: {e}")
        return
        
    # 2. Recursively find Google shortcut files
    print("\nScanning source directory...")
    google_files = []
    for r, dirs, fs in os.walk(root_dir):
        for f in fs:
            ext = os.path.splitext(f)[1].lower()
            if ext in ['.gdoc', '.gsheet']:
                google_files.append(os.path.join(r, f))
                
    total_files = len(google_files)
    print(f"Found {total_files} Google shortcut files.")
    if total_files == 0:
        return
        
    # 3. Process each file
    downloads_dir = get_downloads_folder()
    success_count = 0
    skipped_count = 0
    failed_count = 0
    
    for idx, local_path in enumerate(google_files, 1):
        print(f"\n[{idx}/{total_files}] Processing: {repr(os.path.basename(local_path))}")
        
        # Determine paths and types
        filename = os.path.basename(local_path)
        filename_lower = filename.lower()
        doc_title_no_ext = os.path.splitext(filename)[0]
        
        # Check target extension
        ext = os.path.splitext(local_path)[1].lower()
        if ext == '.gdoc':
            target_ext = '.docx'
            mime_filter = 'application/vnd.google-apps.document'
        elif ext == '.gsheet':
            target_ext = '.xlsx'
            mime_filter = 'application/vnd.google-apps.spreadsheet'
        else:
            print("Unsupported file extension. Skipping.")
            failed_count += 1
            continue
            
        target_path = os.path.join(os.path.dirname(local_path), doc_title_no_ext + target_ext)
        
        # Check if already converted
        if os.path.exists(target_path):
            print(f"Target file already exists. Skipping: {repr(target_path)}")
            skipped_count += 1
            continue
            
        # Match file in the database
        folder_parts = [p.lower() for p in os.path.relpath(local_path, root_dir).split(os.sep)[:-1]]
        matched_item = None
        
        for stable_id, item in items_dict.items():
            if item['title'] and item['title'].lower() == filename_lower and item['mime'] == mime_filter:
                db_parts = get_path_parts(stable_id, items_dict, parents_dict)
                is_match = True
                for part in folder_parts:
                    if part not in db_parts:
                        is_match = False
                        break
                if is_match:
                    matched_item = item
                    break
                    
        if not matched_item:
            print("Warning: Could not match file in Google Drive database. Skipping.")
            failed_count += 1
            continue
            
        drive_id = matched_item['id']
        print(f"Matched Google Drive ID: {drive_id}")
        
        # If dry run, just report match and stop
        if dry_run:
            print(f"[Dry-Run] Would convert to: {target_path}")
            success_count += 1
            continue
            
        # Save original timestamps
        stat = os.stat(local_path)
        orig_atime = stat.st_atime
        orig_mtime = stat.st_mtime
        orig_ctime = stat.st_ctime
        
        # Build Export URL
        if ext == '.gdoc':
            export_url = f"https://docs.google.com/document/d/{drive_id}/export?format=docx"
        else:
            export_url = f"https://docs.google.com/spreadsheets/d/{drive_id}/export?format=xlsx"
            
        expected_download_name = doc_title_no_ext + target_ext
        expected_download_path = os.path.join(downloads_dir, expected_download_name)
        
        # Scan downloads folder before opening browser
        existing_files = set(os.listdir(downloads_dir))
        
        print(f"Opening default browser to download: {expected_download_name}")
        webbrowser.open(export_url)
        
        # Monitor downloads folder for completion (up to 45 seconds)
        print("Waiting for download to complete...")
        start_time = time.time()
        downloaded_file = None
        
        while time.time() - start_time < 45:
            time.sleep(1)
            current_files = set(os.listdir(downloads_dir))
            new_files = current_files - existing_files
            
            for nf in new_files:
                nf_lower = nf.lower()
                if nf_lower == expected_download_name.lower():
                    downloaded_file = os.path.join(downloads_dir, nf)
                    break
                elif nf_lower.startswith(doc_title_no_ext.lower()) and nf_lower.endswith(target_ext):
                    downloaded_file = os.path.join(downloads_dir, nf)
                    break
                    
            if downloaded_file:
                # Make sure it's not a temp download
                if not downloaded_file.endswith('.crdownload') and not downloaded_file.endswith('.tmp'):
                    break
                    
        if downloaded_file:
            print(f"Downloaded file found: {downloaded_file}")
            time.sleep(1.5)  # Wait for file lock release
            
            # Copy to target directory
            try:
                shutil.copyfile(downloaded_file, target_path)
                print(f"Saved: {target_path}")
                
                # Restore timestamps
                os.utime(target_path, (orig_atime, orig_mtime))
                set_windows_creation_time(target_path, orig_ctime)
                print("Restored original metadata created & modified timestamps.")
                
                # Clean up Downloads folder
                try:
                    os.remove(downloaded_file)
                except Exception:
                    pass
                    
                success_count += 1
            except Exception as copy_err:
                print(f"Error copying/saving file: {copy_err}")
                failed_count += 1
        else:
            print("Error: Download timed out or failed to start.")
            failed_count += 1
            
    print("\n" + "=" * 60)
    print("CONVERSION PROCESS COMPLETED")
    print(f"Successful conversions: {success_count}")
    print(f"Already converted (skipped): {skipped_count}")
    print(f"Failed / Unmatched: {failed_count}")
    print("=" * 60)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert local Google Drive shortcuts to Microsoft Office format.")
    parser.add_argument('--dry-run', action='store_true', help="Scan and match files in database without exporting.")
    args = parser.parse_args()
    
    root_dir = r"H:\.shortcut-targets-by-id\1Ck0Y6gTebBnzWmf9IO_auxDwf0XYdNfP\comms kayan"
    convert_files(root_dir, dry_run=args.dry_run)
