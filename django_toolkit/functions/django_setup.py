import django 
import os 
import sys 
from pathlib import Path 


def django_setup(): 
    """ 
    This functions initializes the Django environment. 
    It searches the file manage.py and detects th current directory. 
    """ 

    filename = "manage.py"      # file to be searched 
    caller_file = sys._getframe(1).f_code.co_filename 
    caller_path = Path(caller_file).parent 

    current_path = caller_path 
    while True: 
        filename_to_test = current_path / filename 
        if filename_to_test.is_file() and (current_path / Path(current_path).name / "settings.py").is_file(): 
            break 
        else: 
            if current_path == current_path.parent: 
                raise Exception(f"{filename} not found. Could not setup Django environment") 
            else: 
                current_path = current_path.parent 

    sys.path.append(str(current_path)) 
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"{Path(current_path).name}.settings") 
    django.setup()
