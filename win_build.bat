pyinstaller src\harren\entry_point.py
--hidden-import=pygame --hidden-import=log-color --hidden-
import=six --hidden-import=toml --hidden-import=boltons -p src\harren --add-data=src\harren;harren --onefile
