"""
mapping_test_to_prod.py で得られた結果を反転する．
"""
import json
from collections import defaultdict
from pathlib import Path

from tqdm import tqdm


def main():
    """
    mapping_test_to_prod.py が出力したファイルを取得し，
    反転させる．
    """
    input_root = Path('../result/mapping_test_to_prod').resolve()
    input_files = input_root.rglob('*.json')

    output_root = input_root.parent / Path(__file__).stem
    for input_file in tqdm(input_files):
        with input_file.open() as f:
            orig_dict = json.load(f)

        inverted_dict = invert(orig_dict)

        output_file = output_root.joinpath(*input_file.parts[-2:])
        output_file.parent.mkdir(exist_ok=True, parents=True)
        with output_file.open('w', encoding='utf-8') as f:
            json.dump(inverted_dict, f, indent=4)


def invert(dict_obj: dict) -> dict:
    """
    辞書の対応関係を逆転させる．
    :param dict_obj: 元の辞書．
    :return: 逆転させた辞書．
    """
    inverted_dict = defaultdict(list)
    for key, values in dict_obj.items():
        for value in values:
            inverted_dict[value].append(key)
    return dict(inverted_dict)


if __name__ == '__main__':
    main()
