# to fix bugs reguarding barcode scanner, works and is not needed anymore

import cv2
from pyzbar.pyzbar import decode, ZBarSymbol

def main():
    cap = cv2.VideoCapture(0)
    seen = set()
    print("Point a barcode at the camera. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = decode(frame, symbols=[ZBarSymbol.CODE39])

        for result in results:
            text = result.data.decode("utf-8")
            (x, y, w, h) = result.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, text, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            if text not in seen:
                print(f"Found Code39: {text}")
                seen.add(text)
                import os
                os.system("afplay /System/Library/Sounds/Ping.aiff &")

        cv2.imshow("Barcode Scanner", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()