



# pyinstaller -n "app" --onefile --windowed --clean --icon='files/logo.ico' --add-data="files;files" --add-data="plugins;plugins" --additional-hooks-dir=. --additional-hooks-dir="./plugins" -p ".;./plugins"  --collect-submodules="plugins" ./main.py

pyinstaller -n "LivingPath.spec" --onefile --windowed --clean --icon='files/logo.ico' --add-data="files;files" --additional-hooks-dir="hooks" --splash="files/splash.jpg" --collect-all "hyperglot" -p "." ./main.py

# on MAC OS & unix systems you can write :
# files:files
# (: instead of ;)

# read -rn1 # keep consol open


# ---- mac -------------------------------

# MACOS need conda install -c conda-forge lightgbm


source livingpath/bin/activate
pyinstaller -n "LivingPath.spec" --noconfirm --windowed --icon='files/logo.icns' --add-data="files:files" --additional-hooks-dir="hooks" --collect-all "hyperglot" -p "." ./main.py


# ---- linux -------------------------------

# on windows Ubuntu VM : run "WSL" in power shell
apt get python3.12-full
python3 -m venv dist/LinuxVenv
sudo dist/LinuxVenv/bin/pip install -r requirements.txt
sudo dist/LinuxVenv/bin/pip install --upgrade --force-reinstall freetype-py
sudo apt install ffmpeg

sudo dist/LinuxVenv/bin/pip install scipy==1.11.4



dist/LinuxVenv/bin/python3 main.py

# checked hooks/hooks-iso639.py
# tmp-delete LivingPath.spec (not sure if this has solve the pb)

# delete the playsound stuff => bug on Arch Linux ?

switch hook/tkinterdnd2.py to first one

sudo linux-venv/bin/pyinstaller -n "LivingPath.spec" --onefile --clean --add-data="files:files" --splash="files/splash.jpg" --additional-hooks-dir="hooks" --hidden-import=PIL._tkinter_finder --collect-all "hyperglot" -p "."   ./main.py

 # test exported linux app
 /mnt/c/Users/ivan_/Desktop/code/python/LivingPath/dist/LivingPath
