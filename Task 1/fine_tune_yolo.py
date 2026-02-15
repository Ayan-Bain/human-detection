from ultralytics import YOLO

def fine_tune_human_model():
    model = YOLO('yolov8n.pt')  
    print("Model Loaded")

    print("Starting training...")
    results = model.train(
        data='coco8.yaml',
        epochs=50,
        imgsz=640,
        batch=16,
        name='human-detection',
        
        workers=0,
        
        lr0=0.001,
        optimizer='AdamW',
        dropout=0.0,
        classes=[0]
    )

    print("Exporting...")
    model.export(format='onnx')

if __name__ == '__main__':
    fine_tune_human_model()