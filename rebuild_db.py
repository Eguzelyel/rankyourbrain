import os
import shutil
from datetime import datetime

# Backup the current database
db_path = 'instance/rankyourbrain.db'
if os.path.exists(db_path):
    backup_path = f'instance/rankyourbrain.db.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    shutil.copy2(db_path, backup_path)
    print(f"Backed up database to {backup_path}")
    
    # Remove the current database
    os.remove(db_path)
    print(f"Removed {db_path}")

print("Database has been removed. Run the app to create a new database with the updated schema.")
print("You can do this by running: python app.py")