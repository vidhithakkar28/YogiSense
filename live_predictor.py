def predict_pose(image):
    results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark
        keypoints = []


        for lm in landmarks:
            keypoints.extend([lm.x, lm.y, lm.z])

        if len(keypoints) == 99:
            keypoints = np.array(keypoints).reshape(1, -1)
            keypoints = scaler.transform(keypoints)
            prediction = model.predict(keypoints)[0]
            predicted_label = label_encoder.inverse_transform([prediction])[0]
            return predicted_label, landmarks  # Return both
        else:
            print(f"❌ Expected 99 keypoints but got {len(keypoints)}.")
            return None, None
    else:
        return None, None

