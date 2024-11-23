import subprocess

def run_fall_detection():
    try:
        result = subprocess.run(["python", "./fallDetection/fall_detector.py"], capture_output=True, text=True)
        return result.returncode == 1
    except Exception as e:
        print(f"⚠️ Error al ejecutar la detección de caídas: {e}")
        return False