# main_opencv_lbph_with_presence.py
import os
import time
import cv2
import numpy as np
import pygame
from datetime import datetime

# -------- Konfigurace --------
KNOWN_FACES_DIR = "known_faces"
ALERT_SOUND = "alert.mp3"
CAMERA_INDEX = 0
CONFIDENCE_THRESHOLD =70.0      # nižší = přísnější
ALERT_COOLDOWN = 3.0             # sekundy mezi zvukovými upozorněními
SAVE_COOLDOWN = 2.0              # per-name fallback (nevyužíváme hlavní, máme presence+global)
CAPTURES_DIR = "captures"
ALERT_ONLY_FOR = ["mama", "otec", "sestra" ,"bratr"]  # jména, pro která se přehraje zvuk

# Nové parametry podle tvého požadavku:
MIN_PRESENCE_SECONDS = 1.5      # minimální počet sekund, po které musí být obličej v záběru, aby se uložil
GLOBAL_SAVE_DELAY = 4.0         # globální cooldown mezi uložením jakýchkoli snímků (vteřiny)

# -------- Inicializace zvuku --------
try:
    pygame.mixer.init()
except Exception as e:
    print("⚠️ Pozor: pygame.mixer.init() selhalo:", e)

def play_alert():
    if not os.path.exists(ALERT_SOUND):
        print("⚠️ alert.mp3 nenalezen, zvuk nebude přehrán.")
        return
    try:
        pygame.mixer.music.load(ALERT_SOUND)
        pygame.mixer.music.play()
    except Exception as e:
        print("⚠️ Chyba při přehrávání zvuku:", e)

# -------- Haar cascade ----------
cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(cascade_path)
if face_cascade.empty():
    raise RuntimeError("Nelze načíst Haar cascade: " + cascade_path)

os.makedirs(CAPTURES_DIR, exist_ok=True)

# -------- (stejný trénink LBPH jako dřív) --------
print("🧩 Hledám známé tváře ve složce:", os.path.abspath(KNOWN_FACES_DIR))
if not os.path.isdir(KNOWN_FACES_DIR):
    raise SystemExit("❌ Složka known_faces neexistuje. Vytvoř ji a vlož tam fotky (mama.jpeg, otec.jpeg, ...).")

faces = []
labels = []
label2name = {}
name2label = {}
next_label = 0

for entry in sorted(os.listdir(KNOWN_FACES_DIR)):
    full = os.path.join(KNOWN_FACES_DIR, entry)
    if os.path.isdir(full):
        name = entry
        for fn in sorted(os.listdir(full)):
            fp = os.path.join(full, fn)
            ext = os.path.splitext(fn)[1].lower()
            if ext not in [".jpg", ".jpeg", ".png"]:
                continue
            img = cv2.imread(fp)
            if img is None:
                print("❌ Nelze načíst", fp)
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            rects = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)
            if len(rects) == 0:
                print("⚠️ Obličej nenalezen v", fp)
                continue
            x,y,w,h = max(rects, key=lambda r: r[2]*r[3])
            roi = gray[y:y+h, x:x+w]
            roi = cv2.resize(roi, (200,200))
            if name not in name2label:
                name2label[name] = next_label
                label2name[next_label] = name
                next_label += 1
            faces.append(roi)
            labels.append(name2label[name])
            print("✔ Přidáno (podsložka):", name, fn)
    else:
        ext = os.path.splitext(entry)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png"]:
            continue
        name = os.path.splitext(entry)[0]
        fp = full
        img = cv2.imread(fp)
        if img is None:
            print("❌ Nelze načíst", fp)
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        rects = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)
        if len(rects) == 0:
            print("⚠️ Obličej nenalezen v", fp)
            continue
        x,y,w,h = max(rects, key=lambda r: r[2]*r[3])
        roi = gray[y:y+h, x:x+w]
        roi = cv2.resize(roi, (200,200))
        if name not in name2label:
            name2label[name] = next_label
            label2name[next_label] = name
            next_label += 1
        faces.append(roi)
        labels.append(name2label[name])
        print("✔ Přidáno (file):", name, entry)

if len(faces) == 0:
    print("❌ Nebyly nalezeny žádné trénovací tváře. Ujisti se, že obrázky obsahují jasně viditelnou tvář.")
    raise SystemExit

faces_np = np.array(faces)
labels_np = np.array(labels)

print(f"Trénuji LBPH model na {len(faces)} snímcích, {len(label2name)} osobách...")
try:
    recognizer = cv2.face.LBPHFaceRecognizer_create()
except Exception as e:
    print("❌ cv2.face.LBPHFaceRecognizer_create() selhalo. Máš nainstalovaný opencv-contrib-python?")
    raise
recognizer.train(faces_np, labels_np)
print("✅ Trénink hotov. Mapování štítků:", label2name)

# -------- Proměnné pro ukládání a presence tracking --------
cap = cv2.VideoCapture(CAMERA_INDEX)
if not cap.isOpened():
    raise SystemExit("❌ Nelze otevřít kameru index " + str(CAMERA_INDEX))
print("🎥 Kamera běží. Stiskni 'q' pro ukončení.")

last_alert_time = 0.0
last_global_save_time = 0.0

# trackery: key -> { first_seen, last_seen, saved_flag }
presence = {}  # např. { key: {"first":ts, "last":ts, "saved":False} }

# pomocná funkce pro tvorbu klíče z bboxu a jména
def make_key(name, x, y, w, h, bucket=50):
    cx = x + w//2
    cy = y + h//2
    bx = cx // bucket
    by = cy // bucket
    return f"{name}_{bx}_{by}"

def save_capture(frame_color, name, confidence):
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safe_name = name.replace(" ", "_")
    fname = f"{ts}_{safe_name}_{confidence:.1f}.jpg"
    path = os.path.join(CAPTURES_DIR, fname)
    try:
        cv2.imwrite(path, frame_color)
        print(f"💾 Uloženo: {path}")
    except Exception as e:
        print("⚠️ Chyba při ukládání:", e)

# -------- Hlavní smyčka --------
while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        print("⚠️ Nelze číst z kamery.")
        time.sleep(0.1)
        continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)

    now = time.time()
    seen_keys_this_frame = set()

    for (x,y,w,h) in rects:
        roi = gray[y:y+h, x:x+w]
        try:
            roi_resized = cv2.resize(roi, (200,200))
        except Exception:
            continue
        label, confidence = recognizer.predict(roi_resized)  # nižší = lepší
        name = label2name.get(label, "Neznámý")
        text = f"{name} ({confidence:.1f})"
        color = (0,255,0) if confidence < CONFIDENCE_THRESHOLD else (0,165,255)
        cv2.rectangle(frame, (x,y), (x+w,y+h), color, 2)
        cv2.putText(frame, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        # vytvoříme klíč pro tento hranatá detekce
        key = make_key(name, x, y, w, h, bucket=40)  # bucket=40 -> citlivost pozice
        seen_keys_this_frame.add(key)

        # aktualizuj presence tracker
        if key not in presence:
            presence[key] = {"first": now, "last": now, "saved": False}
        else:
            presence[key]["last"] = now

        # pokud je obličej přítomen dost dlouho a ještě jsme ho neuložili
        duration = now - presence[key]["first"]
        time_since_global = now - last_global_save_time
        if (duration >= MIN_PRESENCE_SECONDS) and (not presence[key]["saved"]) and (time_since_global >= GLOBAL_SAVE_DELAY):
            # uložíme ořez (barevný) z frame
            x0, y0, x1, y1 = max(0,x), max(0,y), min(frame.shape[1], x+w), min(frame.shape[0], y+h)
            crop_color = frame[y0:y1, x0:x1]
            save_capture(crop_color, name, confidence)
            presence[key]["saved"] = True
            last_global_save_time = now  # GLOBAL delay aplikuje se na všechny
            # (nechceme ukládat znovu ihned pro stejného klíče)

        # zvukové upozornění (stejné jako dřív) s cooldownem
        if confidence < CONFIDENCE_THRESHOLD:
            if name.lower() in [n.lower() for n in ALERT_ONLY_FOR]:
                if now - last_alert_time > ALERT_COOLDOWN:
                    print(f"🔔 Rozpoznáno: {name} — confidence={confidence:.1f}")
                    play_alert()
                    last_alert_time = now
            else:
                print(f"(🎧 Rozpoznáno {name}, ale bez zvuku) confidence={confidence:.1f}")

    # čistění presence: pokud nějaký key nebyl viděn delší dobu, vymažeme ho (a umožníme budoucí novou save)
    stale_keys = []
    for key, info in presence.items():
        if now - info["last"] > 1.0:  # pokud nebyl viděn poslední 1s, považujeme za pryč
            stale_keys.append(key)
    for k in stale_keys:
        # odstraněním klíče dovolíme, aby se při dalším opětovném objevení počítalo od nuly
        del presence[k]

    cv2.imshow("Rozpoznávání (LBPH) s ukládáním", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
