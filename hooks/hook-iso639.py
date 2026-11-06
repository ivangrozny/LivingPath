
# ok on win & mac not on linux

# from PyInstaller.utils.hooks import copy_metadata, collect_data_files
# datas = copy_metadata("iso639") + collect_data_files("iso639")


from PyInstaller.utils.hooks import collect_data_files
datas = collect_data_files("iso639")
