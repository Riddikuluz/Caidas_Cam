import subprocess

def run_fall_detection():
    try:
        subprocess.run(["python", "./fallDetection/fall_detector.py"])
    except Exception as e:
        print(f"⚠️ Error al ejecutar la detección de caídas: {e}")
