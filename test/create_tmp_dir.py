import os
from datetime import datetime
import re


tmp_dir = os.path.abspath("./tmp/")
today = datetime.now().strftime("%Y%m%d")

max_id = 0
pattern = f"{today}_test(\d+)"
for item in os.listdir(tmp_dir):
    path = os.path.join(tmp_dir, item)
    if os.path.isdir(path):
        obj = re.search(pattern, path)
        if obj:
            found_id = int(obj.group(1))
            if found_id > max_id:
                max_id = found_id
test_id = max_id + 1

print(str(test_id).zfill(3))
