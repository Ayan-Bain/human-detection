import cv2
from ultralytics import YOLO

def run_custom_model():
    model_path = 'runs/detect/human-detection/weights/best.pt'
    
    try:
        print(f"Loading custom model from: {model_path}")
        model = YOLO(model_path)

    except Exception as e:
        print(f"Error loading model: {e}")
        print("Did you run the training script first? Check the path.")
        return

    cap = cv2.VideoCapture(0)

    print("Starting... Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret: break

        results = model.predict(source=frame, stream=True, conf=0.5, classes=[0], verbose=False)

        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                conf = float(box.conf[0])
                label = f"Human: {int(conf*100)}%"
                
                if(conf>=.85):
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.rectangle(frame, (x1, y1-32), (x1+130, y1-1), (255, 255, 255), -1)
                    cv2.putText(frame, label, (x1+5, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
                else:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
                    cv2.rectangle(frame, (x1, y1-32), (x1+130, y1-1), (0, 191, 255), -1)
                    cv2.putText(frame, label, (x1+5, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,150), 2)

        cv2.imshow('Human Detection', frame)

        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    run_custom_model()