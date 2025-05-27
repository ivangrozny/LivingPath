import os
import platform
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

"""
pyinstaller myproject/myproject.py --additional-hooks-dir=.
"""

print("HOOOOOOOOOOOOOOOOCK TKDND", platform.system())

if platform.system() in ("Windows",'Linux') :
    print("HOOOOOOOOOOOOOOOOCK WIN", platform.system())

    from PyInstaller.utils.hooks import collect_data_files, eval_statement
    datas = collect_data_files('tkinterdnd2')


if platform.system() == "Darwin" :
    print("HOOOOOOOOOOOOOOOOCK MAC", platform.system())

    s = platform.system()
    p = {
        'Windows': ({'win-arm64', 'win-x86', 'win-x64' },{'tkdnd_unix.tcl', 'tkdnd_macosx.tcl'}),
        'Linux': ({'linux-x64', 'linux-arm64'}, {'tkdnd_windows.tcl', 'tkdnd_macosx.tcl'}),
        'Darwin': ({'osx-x64', 'osx-arm64'}, {'tkdnd_windows.tcl', 'tkdnd_unix.tcl'}),
    }
    if s in p:
        datas = set([
            x for x in (
                *collect_data_files('tkinterdnd2'),
                *collect_dynamic_libs('tkinterdnd2'),
            )
            if os.path.split(x[1])[1] in p[s][0] and os.path.split(x[0])[1] not in p[s][1]
        ])
    else:
        raise RuntimeError(f'TkinterDnD2 is not supported on platform "{s}".')
