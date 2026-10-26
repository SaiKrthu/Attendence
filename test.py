import cv2
import pickle
import os
import csv
import time
from datetime import datetime
from sklearn.neighbors import KNeighborsClassifier
from win32com.client import Dispatch


# ============================================================
# TEXT TO SPEECH
# ============================================================

def speak(message):
    speaker = Dispatch("SAPI.SpVoice")
    speaker.Speak(message)


# ============================================================
# LOAD FACE DETECTOR
# ============================================================

facedetect = cv2.CascadeClassifier(
    "data/haarcascade_frontalface_default.xml"
)

if facedetect.empty():
    print("ERROR: Haar Cascade could not be loaded.")
    exit()


# ============================================================
# LOAD TRAINING DATA
# ============================================================

with open("data/names.pkl", "rb") as file:
    LABELS = pickle.load(file)

with open("data/faces_data.pkl", "rb") as file:
    FACES = pickle.load(file)

print("Shape of Faces matrix -->", FACES.shape)
print("Number of Labels -->", len(LABELS))

if len(FACES) != len(LABELS):
    print("ERROR: Faces and labels count do not match.")
    exit()


# ============================================================
# TRAIN KNN
# ============================================================

knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(FACES, LABELS)


# ============================================================
# OPEN CAMERA
# ============================================================

video = cv2.VideoCapture(0)

if not video.isOpened():
    print("ERROR: Camera could not be opened.")
    exit()

# Use normal camera resolution
video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)


# ============================================================
# WINDOW
# ============================================================

WINDOW_NAME = "Face Recognition Attendance System"

cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WINDOW_NAME, 1280, 720)


# ============================================================
# ATTENDANCE VARIABLES
# ============================================================

attendance_message = ""
message_time = 0

last_attendance_time = 0
attendance_cooldown = 5

COL_NAMES = ["NAME", "TIME"]


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    ret, camera_frame = video.read()

    if not ret:
        print("Could not read camera frame.")
        break

    # Mirror camera
    camera_frame = cv2.flip(camera_frame, 1)

    # Resize camera to fill application window
    frame = cv2.resize(camera_frame, (1280, 720))

    # ========================================================
    # FACE DETECTION
    # ========================================================

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = facedetect.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5,
        minSize=(80, 80)
    )

    recognized_name = None
    attendance_data = None

    # ========================================================
    # PROCESS FACE
    # ========================================================

    for (x, y, w, h) in faces:

        crop_img = frame[y:y+h, x:x+w]

        if crop_img.size == 0:
            continue

        resized_img = cv2.resize(
            crop_img,
            (50, 50)
        )

        resized_img = resized_img.flatten().reshape(1, -1)

        prediction = knn.predict(resized_img)

        recognized_name = str(prediction[0])

        # Current date/time
        now = datetime.now()

        date = now.strftime("%d-%m-%Y")
        timestamp = now.strftime("%H:%M:%S")

        attendance_data = [
            recognized_name,
            timestamp
        ]

        # ====================================================
        # FACE BOX
        # ====================================================

        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 230, 160),
            3
        )

        # ====================================================
        # NAME BOX
        # ====================================================

        label_height = 55

        cv2.rectangle(
            frame,
            (x, y - label_height),
            (x + w, y),
            (0, 180, 120),
            -1
        )

        cv2.putText(
            frame,
            recognized_name,
            (x + 15, y - 16),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

    # ========================================================
    # DARK HEADER
    # ========================================================

    cv2.rectangle(
        frame,
        (0, 0),
        (1280, 70),
        (15, 30, 55),
        -1
    )

    # Camera icon
    cv2.rectangle(
        frame,
        (25, 23),
        (58, 48),
        (255, 255, 255),
        2
    )

    cv2.circle(
        frame,
        (42, 35),
        6,
        (255, 255, 255),
        2
    )

    # Title
    cv2.putText(
        frame,
        "FACE RECOGNITION ATTENDANCE SYSTEM",
        (80, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    # ========================================================
    # CAMERA ACTIVE
    # ========================================================

    cv2.circle(
        frame,
        (1130, 35),
        9,
        (0, 230, 150),
        -1
    )

    cv2.putText(
        frame,
        "CAMERA ACTIVE",
        (1150, 41),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 230, 150),
        2,
        cv2.LINE_AA
    )

    # ========================================================
    # BOTTOM ATTENDANCE PANEL
    # ========================================================

    panel_x1 = 300
    panel_y1 = 625
    panel_x2 = 980
    panel_y2 = 700

    cv2.rectangle(
        frame,
        (panel_x1, panel_y1),
        (panel_x2, panel_y2),
        (15, 30, 55),
        -1
    )

    cv2.rectangle(
        frame,
        (panel_x1, panel_y1),
        (panel_x2, panel_y2),
        (0, 230, 160),
        2
    )

    # O button
    cv2.rectangle(
        frame,
        (330, 638),
        (390, 687),
        (0, 230, 160),
        2
    )

    cv2.putText(
        frame,
        "O",
        (348, 674),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.1,
        (255, 255, 255),
        3,
        cv2.LINE_AA
    )

    cv2.putText(
        frame,
        "Press O or 0 to mark attendance",
        (420, 674),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.85,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    # ========================================================
    # SUCCESS MESSAGE
    # ========================================================

    if attendance_message and time.time() < message_time:

        cv2.rectangle(
            frame,
            (350, 275),
            (930, 380),
            (10, 50, 45),
            -1
        )

        cv2.rectangle(
            frame,
            (350, 275),
            (930, 380),
            (0, 230, 160),
            3
        )

        cv2.putText(
            frame,
            attendance_message,
            (395, 340),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 180),
            2,
            cv2.LINE_AA
        )

    # ========================================================
    # DISPLAY FRAME
    # ========================================================

    cv2.imshow(WINDOW_NAME, frame)

    # ========================================================
    # KEYBOARD
    # ========================================================

    key = cv2.waitKey(1) & 0xFF

    # --------------------------------------------------------
    # O OR 0 = ATTENDANCE
    # --------------------------------------------------------

    if key in [ord("o"), ord("O"), ord("0")]:

        if attendance_data is not None:

            name = attendance_data[0]
            timestamp = attendance_data[1]

            attendance_folder = "Attendance"

            os.makedirs(
                attendance_folder,
                exist_ok=True
            )

            attendance_file = os.path.join(
                attendance_folder,
                "Attendance_" + date + ".csv"
            )

            # Prevent accidental repeated attendance
            if time.time() - last_attendance_time >= attendance_cooldown:

                file_exists = os.path.isfile(
                    attendance_file
                )

                with open(
                    attendance_file,
                    "a",
                    newline=""
                ) as csvfile:

                    writer = csv.writer(csvfile)

                    if not file_exists:
                        writer.writerow(COL_NAMES)

                    writer.writerow(
                        [name, timestamp]
                    )

                last_attendance_time = time.time()

                attendance_message = (
                    "Attendance marked: " + name
                )

                message_time = time.time() + 3

                print(
                    f"Attendance marked: {name} - {timestamp}"
                )

                speak(
                    f"Attendance marked for {name}"
                )

        else:

            attendance_message = "No face detected"

            message_time = time.time() + 2

    # --------------------------------------------------------
    # Q = EXIT
    # --------------------------------------------------------

    if key in [ord("q"), ord("Q")]:
        break


# ============================================================
# CLEANUP
# ============================================================

video.release()
cv2.destroyAllWindows()