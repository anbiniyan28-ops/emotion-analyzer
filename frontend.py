import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests
import json

# ----------------------------
# API CONFIG
# ----------------------------
API_URL = "http://127.0.0.1:8000"


# ----------------------------
# MAIN WINDOW
# ----------------------------
root = tk.Tk()
root.title("🧠 Emotion AI Analyzer")
root.geometry("750x600")
root.config(bg="#0f172a")


# ----------------------------
# TITLE
# ----------------------------
title = tk.Label(
    root,
    text="Emotion AI Analyzer",
    font=("Arial", 20, "bold"),
    fg="white",
    bg="#0f172a"
)
title.pack(pady=10)


# ----------------------------
# INPUT BOX
# ----------------------------
tk.Label(root, text="Messages (role: message)", fg="white", bg="#0f172a").pack()

message_box = scrolledtext.ScrolledText(root, height=8, width=85)
message_box.pack(pady=5)


# ----------------------------
# QUESTION INPUT
# ----------------------------
tk.Label(root, text="Question", fg="white", bg="#0f172a").pack()

question_entry = tk.Entry(root, width=85)
question_entry.pack(pady=5)


# ----------------------------
# RESULT BOX
# ----------------------------
tk.Label(root, text="Result", fg="white", bg="#0f172a").pack()

result_box = scrolledtext.ScrolledText(root, height=15, width=85)
result_box.pack(pady=10)


# ----------------------------
# SAFE REQUEST FUNCTION
# ----------------------------
def safe_request(method, endpoint, **kwargs):
    try:
        url = f"{API_URL}{endpoint}"
        response = requests.request(method, url, timeout=15, **kwargs)
        return response

    except requests.exceptions.ConnectionError:
        messagebox.showerror("Error", "Backend not running. Start FastAPI first.")
    except requests.exceptions.Timeout:
        messagebox.showerror("Error", "Request timed out.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

    return None


# ----------------------------
# ANALYZE
# ----------------------------
def analyze():
    text = message_box.get("1.0", tk.END).strip()
    question = question_entry.get().strip()

    if not text or not question:
        messagebox.showerror("Error", "Please enter messages and question")
        return

    messages = []

    for line in text.split("\n"):
        if ":" in line:
            role, content = line.split(":", 1)
            messages.append({
                "role": role.strip(),
                "content": content.strip()
            })

    res = safe_request(
        "POST",
        "/analyze",
        json={
            "messages": messages,
            "question": question
        }
    )

    if not res:
        return

    try:
        data = res.json()
    except:
        data = {"error": "Invalid server response"}

    result_box.delete("1.0", tk.END)
    result_box.insert(tk.END, json.dumps(data, indent=4))


# ----------------------------
# LOAD HISTORY
# ----------------------------
def load_history():
    res = safe_request("GET", "/history")

    if not res:
        return

    try:
        data = res.json()
    except:
        data = {"error": "Invalid response"}

    result_box.delete("1.0", tk.END)
    result_box.insert(tk.END, json.dumps(data, indent=4))


# ----------------------------
# CLEAR HISTORY
# ----------------------------
def clear_history():
    res = safe_request("DELETE", "/history")

    if res:
        messagebox.showinfo("Success", "History cleared")


# ----------------------------
# CHECK BACKEND
# ----------------------------
def check_api():
    res = safe_request("GET", "/")

    if res:
        messagebox.showinfo("API Status", "Backend is running ✔")


# ----------------------------
# BUTTONS
# ----------------------------
btn_frame = tk.Frame(root, bg="#0f172a")
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="Analyze", command=analyze, width=15, bg="#38bdf8").grid(row=0, column=0, padx=5)
tk.Button(btn_frame, text="Load History", command=load_history, width=15, bg="#22c55e").grid(row=0, column=1, padx=5)
tk.Button(btn_frame, text="Clear History", command=clear_history, width=15, bg="#ef4444").grid(row=0, column=2, padx=5)
tk.Button(btn_frame, text="Check API", command=check_api, width=15, bg="#facc15").grid(row=0, column=3, padx=5)


# ----------------------------
# RUN APP
# ----------------------------
root.mainloop()