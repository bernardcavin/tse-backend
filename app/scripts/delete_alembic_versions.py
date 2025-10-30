import os
import glob

# Normalize the path for any OS
versions_dir = os.path.join("app", "core", "database", "alembic", "versions")

if not os.path.exists(versions_dir):
    os.makedirs(versions_dir)
else:
    # Use glob to get all files (not subdirs)
    files = glob.glob(os.path.join(versions_dir, "*"))

    for file_path in files:
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Deleted: {file_path}")



