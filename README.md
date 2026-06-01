# Google Drive Personal Assistant

A powerful, standalone desktop GUI application designed to convert virtual Google Drive shortcut files (`.gdoc`, `.gsheet`) into standard Microsoft Office formats (`.docx`, `.xlsx`) with **perfect metadata timestamp retention** and **complete directory backup options**.

---

## Technical Concept: Google Drive Virtual Sync

> [!IMPORTANT]
> This application is specifically designed and conditioned to operate within the **Google Drive for Desktop** environment.
>
> On Windows, Google Drive for Desktop streams or virtually syncs cloud files to a local drive letter (typically `G:\` or `H:\`). While normal files are accessible locally, Google Workspace documents (`.gdoc` and `.gsheet`) are represented as tiny, virtual shortcut links. 
> 
> Trying to read or copy these files directly using standard text readers or Python's `open()` throws an operating system `Incorrect function` or `Invalid argument` error because they are not actual physical files. 
>
> **How this tool works**: It copies and queries the local Google Drive SQLite metadata database (`metadata_sqlite_db`) under `%LOCALAPPDATA%` to programmatically trace the parent-child folder hierarchy, resolve each shortcut's unique Google Drive File ID, and export it into a real, offline document via your already-authenticated browser session.

---

## Features

- **Database Path-Matching Engine**: Bypasses Windows file locks on virtual files by reading metadata directly from the Google Drive client's local SQLite database.
- **Automated Direct Exports**: Automatically converts Google Docs (`.gdoc` -> `.docx`) and Google Sheets (`.gsheet` -> `.xlsx`) by communicating with Google's export endpoints.
- **Zero-Friction Authentication**: Automatically utilizes your active default browser session (Chrome, Edge, etc.) to securely download the files, eliminating the need to set up complex Google Cloud Platform (GCP) credentials or OAuth consent screens.
- **Metadata Timestamp Restoration**: Reads the exact `CreationTime` and `LastWriteTime` from the original Google shortcut on your filesystem and applies them directly to the newly converted Microsoft Office files, maintaining historical accuracy.
- **Resume Capability (Skip if Exists)**: Scans directories and skips already-converted documents, allowing you to stop and resume the process at any time.
- **Safe Source Deletion**: An optional setting that cleans up folder clutter by deleting the original `.gdoc` / `.gsheet` shortcuts **only** after verifying that a populated, valid Office document has been saved next to it.
- **Complete Directory Backups**: Creates complete, timestamped recursive backups of your source folders prior to conversion, logging the copy status of every file in real time.
- **Responsive Dark-Themed GUI**: A beautiful, modern desktop window built with `tkinter` that runs operations asynchronously on a background thread so the interface never freezes, with an embedded scrolled console that prints unbuffered progress status.

---

## Prerequisites

To run this application, ensure your system meets the following requirements:

1. **Operating System**: Windows (tested on Windows 10/11).
2. **Python Installed**: Python 3.10 or newer must be installed on your computer. (Make sure you check the box **"Add Python to PATH"** during installation).
3. **Google Drive for Desktop**: The official Google Drive for Desktop client must be installed, running, and signed in to your Google account.
4. **Web Browser Session**: You must be signed in to your Google Account on your default web browser (Chrome, Edge, Firefox, etc.) so that the download links can export the files securely without asking for login credentials.

> [!TIP]
> **Zero External Dependencies**: This application runs entirely on Python's built-in standard libraries (`tkinter`, `sqlite3`, `webbrowser`, `threading`, etc.). There is **no need** to install any external python packages via `pip`.

---

## Step-by-Step Guide

Follow these steps to run and use the application on your computer:

### Step 1: Download the Project
- Clone this repository or download the ZIP archive of the project and extract the contents to a folder on your computer (e.g., `d:\projects\google-drive-assistant`).

### Step 2: Open the Application
- Open the project directory in Windows File Explorer.
- Double-click **`run_app.bat`**. This will launch the graphical interface instantly.
- *Alternative*: Open PowerShell or Command Prompt, navigate to the folder, and run:
  ```powershell
  py GoogleDriveConverterApp.py
  ```

### Step 3: Select the Google Drive Folder
- In the **Select Source Folder** field, click the **Browse...** button.
- Navigate to your virtual Google Drive disk (usually `G:\` or `H:\`), open `My Drive` or `Other computers`, and select the specific folder containing the `.gdoc` and `.gsheet` shortcuts you want to convert.

### Step 4: Configure Options (Optional)
- **Backup Folder**: Check the *\"Backup source directory before starting conversion\"* box, click **Browse...** next to the backup entry, and choose a safe location on your local drive (like `D:\Backups`) where a timestamped backup of all files will be created first.
- **Dry-Run Only**: Check this box if you want to perform a safe run first to verify that all your shortcuts can be matched to their Google Drive IDs in the database, without actually initiating any browser downloads.
- **Safely Delete Shortcuts**: Check this box if you want the application to automatically delete the old `.gdoc`/`.gsheet` shortcut files *only* after confirming a matching, valid `.docx`/`.xlsx` file has been saved in its place.

### Step 5: Start the Process
- Click the big **Start Backup & Conversion Process** button.
- The logger console at the bottom will start displaying real-time unbuffered progress logs.
- Your browser will briefly open tabs to download the files sequentially, which will automatically be placed in your destination folders with their original creation/modification dates intact.

---

## Business Value

### For Personal Users
- **Offline Independence**: Move your personal documents out of Google's cloud-only format and into standard Microsoft Office files that you can edit, back up, and access fully offline.
- **Data Preservation**: Safeguard personal memories, tax documents, and letters by automatically backing up your files to a local drive before doing any format conversions.
- **Ease of Use**: A simple double-clickable desktop interface with no command-line typing or software configuration required.

### For Business Users
- **Corporate Compliance & Audit Readiness**: Retaining the exact original filesystem `CreationTime` and `LastWriteTime` ensures that corporate archiving, legal holds, and strict regulatory compliance guidelines are fully respected.
- **Seamless B2B Collaboration**: Easily convert Google Workspace folders into standard `.docx` and `.xlsx` formats, making it simple to collaborate with clients and partners who operate exclusively on Microsoft Office 365.
- **Storage & Clutter Minimization**: Clean up shared directories by safely sweeping away old cloud-link shortcuts once the converted Office assets are successfully verified and secured.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
