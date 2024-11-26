"""
PyNose の結果は約 2 TB存在するのでそれらを圧縮するプログラム．
"""
import json
from pathlib import Path
from tqdm import tqdm

from pynose_result_manager import PyNoseResultManager


this_file_name = Path(__file__).stem
output_root = Path(f'../result/{this_file_name}')
output_root.mkdir(exist_ok=True)


input_root = Path('../result/execute_pynose_per_commit').resolve()

# リポジトリ単位のループ
for repo_dir in tqdm(input_root.glob('*')):
    output_repo_dir = output_root.joinpath(repo_dir.name)
    output_repo_dir.mkdir(exist_ok=True)

    # 各JSONファイルのループ
    for json_file_path in tqdm(repo_dir.glob('*.json'), leave=False):
        output_file_name = json_file_path.name
        pynose_result_manager = PyNoseResultManager(json_file_path)
        json_data = pynose_result_manager.count_test_smells_per_file()
        with output_repo_dir.joinpath(output_file_name).open('w') as f:
            json.dump(json_data, f)
