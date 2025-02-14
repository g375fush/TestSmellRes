"""
テストスメルの出現割合や，バグとの関係性を分析する．
"""
import copy
import json
from pathlib import Path


def main():
    """
    統合されたデータからテストスメルやバグのデータを取得して
    表形式に情報を出力する．
    """
    with Path(f'../result/data_forge/aggregated.json').open() as f:
        forged_data: dict = json.load(f)

    bug_list = get_bug_data(forged_data)
    smells_list = get_smell_data(forged_data)
    files_count = get_the_number_of_files(forged_data)

    show_smell_appearance_table(smells_list, files_count)
    show_bug_and_smell_relation_table(bug_list, smells_list)
    show_bug_and_smell_appearance_kind_table(bug_list, smells_list)


def get_the_number_of_files(forged_data: dict) -> int:
    """
    対象となった製品コードの総数を取得する．
    :param forged_data: 解析に必要なデータが一元管理されている辞書．
    """
    file_count = 0
    for url, files in forged_data.items():
        for file_path, _ in files.items():
            file_count += 1
    return file_count


def get_bug_data(forged_data: dict) -> list:
    """
    バグかどうかを表す数値を取得する．
    :param forged_data: 解析に必要なデータが一元管理されている辞書．
    """
    bug_data = []
    for url, files in forged_data.items():
        for file_path, metrics in files.items():
            bug_data.append(metrics['bug'])
    return bug_data


def get_smell_data(forged_data: dict) -> list[dict]:
    """
    テストスメルのデータを取得する．
    :param forged_data: 解析に必要なデータが一元管理されている辞書．
    """
    smells_list = []
    for url, files in forged_data.items():
        for file_path, metrics in files.items():
            smells_list.append(metrics['pynose_result'])
    return smells_list


def show_smell_appearance_table(smells_list: list[dict], files_count: int):
    """
    どのテストスメルがどれほど出現しているのかを計算して表示する．
    スメル自体がどれほど出現するかも表示する．
    """
    smell_appearance = {}
    any_appearance = {}
    for smells in smells_list:
        any_smell = False
        for smell, count in smells.items():
            if count:
                smell_appearance[smell] = smell_appearance.get(smell, 0) + 1
                any_smell = True
        if any_smell:
            any_appearance['any'] = any_appearance.get('any', 0) + 1

    print("="*15 + 'smell appearance' + "="*15)
    for name, appearance in smell_appearance.items():
        rate = f'{100*appearance/files_count:>5.2f}%'
        print(f'{name:30} {appearance:4d}/{files_count:4d} {rate}')

    any_count = any_appearance['any']
    rate = f'{100*any_count/files_count:>.2f}%'
    print(f'{"any":30} {any_count:4}/{files_count:4} {rate}')
    print('\n\n')


def show_bug_and_smell_relation_table(bug_list: list, smells_list: list[dict]):
    """
    テストスメルがついている下での条件付きバグ率と，
    製品コードのバグ率を算出して表示する．
    """
    bug_and_smell_combination = {}
    smell_appearance = {}
    for smells, bug in zip(smells_list, bug_list):
        for smell, count in smells.items():
            if count:
                smell_appearance[smell] = smell_appearance.get(smell, 0) + 1
            if count and bug:
                bug_and_smell_combination[smell] \
                    = bug_and_smell_combination.get(smell, 0) + 1

    print("="*15 + 'bug and smell relation' + "="*15)
    for name, combination in bug_and_smell_combination.items():
        rate = f'{100*combination/smell_appearance[name]:>4.1f}%'
        print(f'{name:30} {combination:4d}/{smell_appearance[name]:4d} {rate}')

    rate = f'{100*bug_list.count(1)/len(bug_list):>4.1f}%'
    print(f'{"bug":30} {bug_list.count(1):4d}/{len(bug_list):4d} {rate}')
    print('\n\n')


def show_bug_and_smell_appearance_kind_table(bug_list, smells_list):
    """
    テストスメルの出現種類数を計算して平均を算出する．
    そして，条件付きバグ率を算出する．
    ただし，Default Test は除外する．
    """
    filtered_smells_list = copy.deepcopy(smells_list)
    for smells in filtered_smells_list:
        smells.pop('DefaultTest')

    smell_kind_list = []
    for smells in filtered_smells_list:
        smell_kind_list.append(sum(bool(smell) for smell in smells.values()))
    ave = sum(smell_kind_list) / len(smell_kind_list)

    zero = 0
    zero_and_bug = 0

    below_ave = 0
    below_ave_and_bug = 0

    above_ave = 0
    above_ave_and_bug = 0
    for smells, bug in zip(filtered_smells_list, bug_list):
        smell_kind = sum(bool(smell) for smell in smells.values())
        if smell_kind == 0:
            zero += 1
            if bug:
                zero_and_bug += 1
        elif smell_kind < ave:
            below_ave += 1
            if bug:
                below_ave_and_bug += 1
        else:
            above_ave += 1
            if bug:
                above_ave_and_bug += 1

    print("=" * 15 + 'bug and smell kind relation' + "=" * 15)
    print(f'ave {ave:4.2f}')
    print(f'    0 {zero_and_bug}/{zero:4d} {100*zero_and_bug/zero:3.1f}')
    rate = f'{100*below_ave_and_bug/below_ave:3.1f}'
    print(f'~{ave:4.2f} {below_ave_and_bug}/{below_ave} {rate}')
    rate = f'{100*above_ave_and_bug/above_ave:3.1f}'
    print(f'{ave:4.2f}~ {above_ave_and_bug}/{above_ave} {rate}')

    rate = f'{100 * bug_list.count(1) / len(bug_list):>4.1f}%'
    print(f'bug:{bug_list.count(1):4d}/{len(bug_list):4d} {rate}')


if __name__ == '__main__':
    main()
