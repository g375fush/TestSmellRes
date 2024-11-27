"""
Ctrl + c などによってたまに PyNose の出力する json ファイルが破損することがある．
それらを検出し，削除するプログラム．
具体的には，ファイルの読み込みに失敗するか，解析に失敗した場合に削除する．
"""
from pathlib import Path

from tqdm import tqdm

from pynose_result_manager import PyNoseResultManager


result_root = Path('../result/execute_pynose_per_commit').resolve(strict=True)
pynose_result_paths = result_root.rglob('*.json')

for pynose_result_path in tqdm(pynose_result_paths):
    try:
        pynose_result_manager = PyNoseResultManager(pynose_result_path)
        pynose_result_manager.count_test_smells_per_file()
    except KeyboardInterrupt:
        break
    except: # noqa
        print(pynose_result_path.as_posix())
        pynose_result_path.unlink()
