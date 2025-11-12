import time
import subprocess

print("⏳ Waiting 15 seconds for Lambda update to complete...")
time.sleep(15)

print("\n🧪 Running OpenSearch test...")
subprocess.run(["python", "wait_and_test_opensearch.py"])
