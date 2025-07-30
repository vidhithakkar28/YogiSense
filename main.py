import tkinter as tk
from tkinter import ttk
import json
import webbrowser
from PIL import Image, ImageTk
import io
import requests
import cv2
import mediapipe as mp
from time import time
import threading

# Load JSON data
with open('asanas.json', 'r', encoding='utf-8') as file:
    asanas = json.load(file)

from get_pose_feedback import get_pose_feedback


def get_asanas_by_level(level):
    return [asana for asana in asanas if asana["level"].lower() == level.lower()]


def get_asana_by_name(name):
    for asana in asanas:
        if asana["asana_name_en"].lower() == name.lower():
            return asana
    return None


def open_link(url):
    webbrowser.open(url)


# -----------------------
import cv2
from time import time
from get_pose_feedback import get_pose_feedback  # Make sure this is correct


def show_auto_popup(message):
    feedback_popup = tk.Toplevel()
    feedback_popup.title("Correction Needed")
    feedback_popup.geometry("300x100+1000+100")
    feedback_popup.configure(bg="#fff0f0")
    feedback_popup.attributes("-topmost", True)

    label = tk.Label(
        feedback_popup,
        text=f"Fix: {message}",
        bg="#fff0f0",
        fg="red",
        font=("Helvetica", 16, "bold"),
        wraplength=280
    )
    label.pack(expand=True, fill="both", padx=10, pady=10)

    feedback_popup.lift()
    feedback_popup.after(3000, feedback_popup.destroy)


def try_pose(asana_name):
    print("🧘‍♀️ Analyzing:", asana_name)

    import mediapipe as mp
    mp_drawing = mp.solutions.drawing_utils
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    correct_start_time = None
    hold_time_needed = 30
    timer_started = False
    frame_id = 0
    popup_cooldown = {}
    feedback_consistency = {}
    required_consistency = 3
    popup_shown_parts = set()

    cv2.namedWindow("Yoga Pose Correction", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Yoga Pose Correction", 900, 600)

    start_time = time()  # start global timer

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        current_time = time()
        if current_time - start_time >= 60:
            cap.release()
            cv2.destroyAllWindows()
            root = tk.Tk()
            root.withdraw()
            from tkinter import messagebox
            ask = messagebox.askyesno("Great Effort ✨",
                                      f"You practiced {asana_name} for 60 seconds!\nYou did it well 🌟\nWanna try again?")
            root.destroy()
            if ask:
                try_pose(asana_name)
            return

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)
        draw_frame = frame.copy()
        frame_id += 1

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            feedback = get_pose_feedback(asana_name, landmarks, frame_id=frame_id)

            mp_drawing.draw_landmarks(draw_frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            if len(feedback) >= 2:
                correct_start_time = None
                timer_started = False

                now = time()
                for part in feedback:
                    feedback_consistency[part] = feedback_consistency.get(part, 0) + 1

                    if feedback_consistency[part] >= required_consistency:
                        if popup_cooldown.get(part, 0) + 4 < now and part not in popup_shown_parts:
                            print(f"🔔 Showing consistent popup for: {part}")
                            show_auto_popup(part)
                            popup_cooldown[part] = now
                            popup_shown_parts.add(part)
                            feedback_consistency[part] = 0

            else:
                feedback_consistency.clear()
                popup_shown_parts.clear()

                if not timer_started:
                    correct_start_time = time()
                    timer_started = True

                held_time = int(time() - correct_start_time)
                cv2.putText(draw_frame, f"✅ Hold: {held_time}s", (30, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

                if held_time >= hold_time_needed:
                    cap.release()
                    cv2.destroyAllWindows()
                    root = tk.Tk()
                    root.withdraw()
                    from tkinter import messagebox
                    ask = messagebox.askyesno("Well Done 💪",
                                              f"You held the {asana_name} pose for {hold_time_needed} seconds!\nWanna try again?")
                    root.destroy()
                    if ask:
                        try_pose(asana_name)
                    return

        else:
            correct_start_time = None
            timer_started = False
            cv2.putText(draw_frame, "🔍 Pose not detected!", (30, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        cv2.imshow("Yoga Pose Correction", draw_frame)
        if cv2.waitKey(10) & 0xFF == ord('q') or cv2.getWindowProperty("Yoga Pose Correction",
                                                                       cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()


def show_asana_popup(asana_name):
    asana = get_asana_by_name(asana_name)
    if not asana:
        print("Asana not found!")
        return

    bg_color = "#FFD9DC"
    text_color = "#3C3148"

    win = tk.Toplevel()
    win.title(asana["asana_name_en"] + " Details")
    win.configure(bg=bg_color)
    win.geometry("880x600")

    title = tk.Label(win, text=asana["asana_name_en"] + " (" + asana["asana_name_sanskrit"] + ")",
                     font=("Trebuchet MS", 25, "bold"), bg=bg_color, fg=text_color)
    title.pack(pady=15)

    content_frame = tk.Frame(win, bg=bg_color)
    content_frame.pack(pady=10, padx=20, fill="both", expand=True)

    text_frame = tk.Frame(content_frame, bg=bg_color)
    text_frame.pack(side="left", fill="both", expand=True)

    def add_text(label, text):
        tk.Label(text_frame, text=label, font=("Trebuchet MS", 14, "bold"),
                 bg=bg_color, fg=text_color).pack(anchor="w", pady=3)
        tk.Label(text_frame, text=text, wraplength=500, justify="left",
                 bg=bg_color, fg="#2e2e2e", font=("Trebuchet MS", 12)).pack(anchor="w", pady=2)

    add_text("🧘 Level:", asana["level"])
    add_text("🌿 Benefits:", asana["benefits"])
    add_text("⚠️ Cautions:", asana["cautions"])
    add_text("💊 Helps With:", asana["diseases_helped"])
    add_text("💪 Improves:", asana["body_parts_improved"])

    image_frame = tk.Frame(content_frame, bg=bg_color)
    image_frame.pack(side="right", padx=10)

    try:
        img_path = asana.get("image_url") or asana.get("image")
        if img_path.lower().startswith("http"):
            response = requests.get(img_path)
            image = Image.open(io.BytesIO(response.content)).resize((280, 210))
        else:
            image = Image.open(img_path).resize((280, 210))
        photo = ImageTk.PhotoImage(image)
        img_label = tk.Label(image_frame, image=photo, bg=bg_color)
        img_label.image = photo
        img_label.pack()

    except:
        tk.Label(image_frame, text="(Image preview failed.)", fg="red", bg=bg_color).pack()

    btn_frame = tk.Frame(win, bg=bg_color)
    btn_frame.pack(pady=10)

    yt_btn = ttk.Button(btn_frame, text="▶ Watch on YouTube",
                        command=lambda: open_link(asana["youtube_url"]),
                        style="Custom.TButton")
    yt_btn.grid(row=0, column=0, padx=10)

    try_btn = ttk.Button(btn_frame, text="💪 Let's Try It!",
                         command=lambda: threading.Thread(target=try_pose, args=(asana_name,)).start(),
                         style="Custom.TButton")
    try_btn.grid(row=0, column=1, padx=10)


def show_asana_selector(level):
    level_asanas = get_asanas_by_level(level)
    if not level_asanas:
        return

    root = tk.Toplevel()
    root.title(f"{level.capitalize()} Asanas")
    root.geometry("450x200")
    root.configure(bg="#FFD9DC")

    tk.Label(root, text=f"🔄 Select a {level.capitalize()} Asana", font=("Helvetica", 16, "bold"),
             bg="#FFD9DC", fg="#3C3148").pack(pady=20)

    asana_names = [asana["asana_name_en"] for asana in level_asanas]

    selected_asana = tk.StringVar()
    combo = ttk.Combobox(root, textvariable=selected_asana, values=asana_names, width=40, state="readonly")
    combo.pack(pady=10)
    combo.set("Choose a pose...")

    ttk.Button(root, text="✨ Show Asana Details", style="Custom.TButton",
               command=lambda: show_asana_popup(combo.get())).pack(pady=15)


def main_landing():
    win = tk.Tk()
    win.title("Yoga Levels")
    win.geometry("500x300")
    win.configure(bg="#FFD9DC")

    tk.Label(win, text="🧘 Choose Your Yoga Level", font=("Helvetica", 18, "bold"),
             bg="#FFD9DC", fg="#3C3148").pack(pady=25)

    btn_frame = tk.Frame(win, bg="#FFD9DC")
    btn_frame.pack(pady=20)

    ttk.Button(btn_frame, text="🍼 Beginner", style="Custom.TButton",
               command=lambda: show_asana_selector("Beginner")).grid(row=0, column=0, padx=10)

    ttk.Button(btn_frame, text="🔥 Intermediate", style="Custom.TButton",
               command=lambda: show_asana_selector("Intermediate")).grid(row=0, column=1, padx=10)

    ttk.Button(btn_frame, text="🚀 Advanced", style="Custom.TButton",
               command=lambda: show_asana_selector("Advanced")).grid(row=0, column=2, padx=10)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Custom.TButton",
                    font=("Helvetica", 11, "bold"),
                    foreground="white",
                    background="#3C3148",
                    padding=8,
                    borderwidth=0)
    style.map("Custom.TButton",
              background=[("active", "#5A4B6B")],
              foreground=[("active", "#ffffff")])

    win.mainloop()


# Run it 💖
main_landing()
