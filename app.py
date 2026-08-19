# explain how it works
# rolls for the period are preloaded into the database
# eventually have a student view and teacher view - teacher can see student class, debug, etc
# ALSO INCLUDE SAFETY FEATURES IN HERE

# make the export csv more functional? - find a way to export the whole 'log' from db

# most database setup function could be moved to a separate file for simplicity


import cv2
import tkinter as tk
from tkinter import ttk, simpledialog, filedialog, messagebox
from PIL import Image, ImageTk
from pyzbar.pyzbar import decode, ZBarSymbol
import os
import sqlite3
import time
import csv
from datetime import datetime
import fill_role

DB_NAME = "attendance.db"

# -------------------------------------------------------------------
# DATABASE FUNCTIONS
# -------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            period INTEGER NOT NULL DEFAULT 1,
            class_name TEXT NOT NULL DEFAULT ''
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS presence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            action TEXT NOT NULL,
            reason TEXT DEFAULT '',
            event_time TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    conn.close()

def seed_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Preloaded users with period and class_name included
    sample_users = [
        ("100125", "Alex Smith", 1, "12STU2"),
        ("100126", "John Doe", 1, "12PHY"),
        ("100127", "Jane Miller", 1, "12ENA"),
        ("100128", "Taylor Reed", 1, "12STU2")
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO users (user_id, name, period, class_name) VALUES (?, ?, ?, ?)
    """, sample_users)

    conn.commit()
    conn.close()

def process_scan(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT action FROM presence 
        WHERE user_id = ? 
        ORDER BY id DESC LIMIT 1
    """, (user_id,))
    row = cursor.fetchone()

    if row is None or row[0] == "sign_out":
        action = "sign_in"
    else:
        action = "sign_out"

    cursor.execute("""
        INSERT INTO presence (user_id, action, reason, event_time)
        VALUES (?, ?, '', time('now', 'localtime'))
    """, (user_id, action))

    log_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return action, log_id

def update_reason(log_id, reason):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE presence
        SET reason = ?
        WHERE id = ?
    """, (reason, log_id))

    conn.commit()
    conn.close()

def get_latest_user_states():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            u.user_id,
            u.name,
            u.period,
            u.class_name,
            latest.action,
            (
                SELECT event_time FROM presence 
                WHERE user_id = u.user_id AND action = 'sign_in' 
                ORDER BY id DESC LIMIT 1
            ) AS last_sign_in,
            (
                SELECT event_time FROM presence 
                WHERE user_id = u.user_id AND action = 'sign_out' 
                ORDER BY id DESC LIMIT 1
            ) AS last_sign_out,
            (
                SELECT reason FROM presence 
                WHERE user_id = u.user_id AND action = 'sign_out' 
                ORDER BY id DESC LIMIT 1
            ) AS last_reason
        FROM users u
        LEFT JOIN (
            SELECT p1.*
            FROM presence p1
            INNER JOIN (
                SELECT user_id, MAX(id) as max_id
                FROM presence
                GROUP BY user_id
            ) p2 ON p1.id = p2.max_id
        ) latest ON u.user_id = latest.user_id
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows

def get_current_period():
    """Fetches the period setting from the first user record (defaults to 1)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT period FROM users LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 1

def clear_presence_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM presence;")
    conn.commit()
    conn.close()


# -------------------------------------------------------------------
# GUI APPLICATION
# -------------------------------------------------------------------
class BarcodeScannerApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Barcode Attendance Log")

        # Fullscreen / Maximized Setup
        try:
            self.window.tk.call('wm', 'attributes', '.', '-zoomed', True)
        except tk.TclError:
            self.window.state('zoomed')

        self.cap = cv2.VideoCapture(0)
        self.last_scanned = {}
        self.cooldown_seconds = 4

        # Top Header Frame: Date & Period Label
        header_frame = tk.Frame(window, bg="#e2e8f0", pady=8)
        header_frame.pack(side=tk.TOP, fill=tk.X)

        current_date_str = datetime.now().strftime("%A, %B %d, %Y")
        current_period = get_current_period()

        self.header_label = tk.Label(
            header_frame,
            text=f"Date: {current_date_str}   |   Current Period: {current_period}",
            font=("Arial", 12, "bold"),
            bg="#e2e8f0",
            fg="#1e293b"
        )
        self.header_label.pack()

        # Left Column: Video Feed & Action Buttons below webcam
        left_frame = tk.Frame(window)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=15, pady=15)

        self.video_label = tk.Label(left_frame, width=640, height=480, bg="#000000")
        self.video_label.pack(side=tk.TOP)

        controls_frame = tk.Frame(left_frame)
        controls_frame.pack(side=tk.TOP, fill=tk.X, pady=(15, 0))

        export_btn = tk.Button(
            controls_frame,
            text="Export CSV",
            font=("Arial", 10, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            padx=14,
            pady=6,
            command=self.export_to_csv
        )
        export_btn.pack(side=tk.LEFT, padx=(0, 10))

        reset_btn = tk.Button(
            controls_frame,
            text="DEBUG_Reset Presence DB",
            font=("Arial", 10, "bold"),
            bg="#dc2626",
            fg="#ffffff",
            padx=14,
            pady=6,
            command=self.reset_db
        )
        reset_btn.pack(side=tk.LEFT)

        # Right Column: Attendance Table
        right_frame = tk.Frame(window)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=15, pady=15)

        tk.Label(right_frame, text="Attendance Log", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 10))

        table_frame = tk.Frame(right_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Frontend Table excludes 'class' and 'id' columns
        columns = ("id", "name", "period", "status", "sign_in", "sign_out", "reason")
        self.tree = ttk.Treeview(
            table_frame, 
            columns=columns, 
            show="headings", 
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tree.yview)

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("period", text="Period")
        self.tree.heading("status", text="Status")
        self.tree.heading("sign_in", text="Sign In Time")
        self.tree.heading("sign_out", text="Sign Out Time")
        self.tree.heading("reason", text="Reason")

        self.tree.column("id", width=70, anchor="center")
        self.tree.column("name", width=130)
        self.tree.column("period", width=60, anchor="center")
        self.tree.column("status", width=90, anchor="center")
        self.tree.column("sign_in", width=110, anchor="center")
        self.tree.column("sign_out", width=110, anchor="center")
        self.tree.column("reason", width=130)

        self.tree.pack(fill=tk.BOTH, expand=True)

        self.refresh_table()
        self.update_frame()
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        records = get_latest_user_states()
        # Unpacks class_name but does not insert it into self.tree values
        for user_id, name, period, class_name, last_action, sign_in_time, sign_out_time, reason in records:
            if last_action is None:
                status_text = "Absent"
            elif last_action == "sign_in":
                status_text = "Here"
            else:
                status_text = "Signed Out"

            self.tree.insert(
                "", 
                tk.END, 
                values=(
                    user_id, 
                    name, 
                    period,
                    status_text, 
                    sign_in_time or "Not Scanned", 
                    sign_out_time or "", 
                    reason or ""
                )
            )

    def export_to_csv(self):
        now = datetime.now()
        current_period = get_current_period()
        
        default_filename = f"attendance_{now.strftime('%Y-%m-%d')}_period{current_period}.csv"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=default_filename,
            title="Export Attendance Summary"
        )

        if not file_path:
            return

        try:
            records = get_latest_user_states()
            export_date_str = now.strftime("%Y-%m-%d")

            with open(file_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)

                # Header Metadata Block
                writer.writerow(["ATTENDANCE REPORT"])
                writer.writerow(["Date:", export_date_str])
                writer.writerow(["Period:", current_period])
                writer.writerow([])  # Blank spacer row

                # Table Column Headers (Includes Class)
                writer.writerow(["User ID", "Name", "Class", "Period", "Status", "Sign In Time", "Sign Out Time", "Reason"])

                for user_id, name, period, class_name, last_action, sign_in_time, sign_out_time, reason in records:
                    if last_action is None:
                        status_text = "Absent"
                    elif last_action == "sign_in":
                        status_text = "Here"
                    else:
                        status_text = "Signed Out"

                    writer.writerow([
                        user_id,
                        name,
                        class_name,
                        period,
                        status_text,
                        sign_in_time or "Not Scanned",
                        sign_out_time or "",
                        reason or ""
                    ])

            messagebox.showinfo("Export Successful", f"Saved successfully to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export file:\n{str(e)}")

    def reset_db(self):
        confirm = messagebox.askyesno(
            "Confirm Reset", 
            "Are you sure you want to clear all presence records?\nThis cannot be undone.",
            icon="warning"
        )
        if confirm:
            clear_presence_db()
            self.refresh_table()
            messagebox.showinfo("Reset Complete", "All presence records have been cleared.")

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.resize(frame, (640, 480))
            results = decode(frame, symbols=[ZBarSymbol.CODE39])
            current_time = time.time()

            for result in results:
                text = result.data.decode("utf-8")
                (x, y, w, h) = result.rect

                last_time = self.last_scanned.get(text, 0)
                
                if (current_time - last_time) > self.cooldown_seconds:
                    self.last_scanned[text] = current_time
                    
                    action, log_id = process_scan(user_id=text)
                    self.refresh_table()
                    os.system("afplay /System/Library/Sounds/Ping.aiff &")

                    if action == "sign_out":
                        reason = simpledialog.askstring(
                            "Sign Out Reason", 
                            f"Enter reason for sign-out (optional):",
                            parent=self.window
                        )
                        if reason:
                            update_reason(log_id, reason)
                            self.refresh_table()

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, text, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2_image)
            imgtk = ImageTk.PhotoImage(image=img)

            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        self.window.after(10, self.update_frame)

    def on_close(self):
        self.cap.release()
        self.window.destroy()

if __name__ == "__main__":
    fill_role.create_db()
    fill_role.create_users() # check if this works!

    root = tk.Tk()
    app = BarcodeScannerApp(root)
    root.mainloop()