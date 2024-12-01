"""
PyNose の結果は約 2 TB存在するのでそれらを圧縮するプログラム．
"""
import json
from pathlib import Path

from tqdm import tqdm

from pynose_result_manager import PyNoseResultManager


def main():
    """
    不必要な情報を省き，見やすさを排除することで圧縮を図る．
    """
    input_root = Path('../result/execute_pynose_per_commit').resolve()
    input_files = [file_path for result_dir in input_root.iterdir()
                   for file_path in result_dir.glob('*.json')]

    this_file_name = Path(__file__).stem
    output_root = Path(f'../result/{this_file_name}').resolve()
    output_root.mkdir(exist_ok=True)

    for result_dir in input_root.iterdir():
        output_root.joinpath(result_dir.name).mkdir(exist_ok=True)

    output_files = [output_root.joinpath(*file_path.parts[-2:])
                    for file_path in input_files]

    for input_file, output_file in zip(tqdm(input_files), output_files):
        manager = PyNoseResultManager(input_file)
        compressed_data = manager.count_test_smells_per_file()

        with output_file.open('w') as f:
            json.dump(compressed_data, f)


if __name__ == '__main__':
    main()
