pyinstaller ^
--add-data="find_albumless_media.py:." ^
--add-data="web_bot_controller.py:." ^
--add-data="web_bot_functions.py:." ^
--add-data="workers.py:." ^
--add-data="GPAT dark mode v2.ico:." ^
--add-data="GPAT light mode v2.ico:." ^
-i="GPAT light mode v2.ico" ^
"GP Albumless tracker.py"
pause

REM --add-data="find_albumless_media.py:." --add-data="web_bot_controller.py:." --add-data="web_bot_functions.py:." --add-data="workers.py:."