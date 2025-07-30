import numpy as np
import mediapipe as mp
import json

# Load ideal pose data
with open("pose_data.json", "r") as f:
    ideal_poses = json.load(f)

mp_pose = mp.solutions.pose

# Global memory to track part errors across frames
frame_error_memory = {}

def get_pose_feedback(pose_name, landmarks, threshold=0.12, frame_id=0):
    feedback = []

    # Get ideal data for the pose
    ideal = ideal_poses.get(pose_name)
    if not ideal:
        return ["🤷 Ideal data for this pose is not available."]

    # Calculate dynamic body scale (shoulder to hip distance)
    try:
        shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        body_scale = np.linalg.norm([shoulder.x - hip.x, shoulder.y - hip.y])
    except:
        body_scale = 1.0  # Fallback if landmarks not detected

    global frame_error_memory
    if frame_id == 0:
        frame_error_memory = {}  # Reset tracking when new session starts

    for key, ideal_coords in ideal.items():
        try:
            landmark_enum = getattr(mp_pose.PoseLandmark, key.upper())
            live_coords = landmarks[landmark_enum.value]

            live_point = np.array([live_coords.x, live_coords.y])
            ideal_point = np.array(ideal_coords)

            distance = np.linalg.norm(live_point - ideal_point)
            relative_error = distance / body_scale

            # 🔍 Debug log for each part
            print(f"🔍 {key.replace('_', ' ').title()} → Δ: {distance:.4f} | Scaled: {relative_error:.4f}")

            # Track consistent errors across frames
            if relative_error > threshold:
                frame_error_memory[key] = frame_error_memory.get(key, 0) + 1
            else:
                frame_error_memory[key] = 0

            if frame_error_memory[key] >= 3:  # only if wrong in 3+ frames
                feedback.append(key.replace("_", " ").title())

        except Exception as e:
            continue

    return feedback[:4]  # Limit feedback to top 4 issues

