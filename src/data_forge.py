"""
今までのデータを統合し，実際に使用できるデータ型にする．
ただし，間引きなどの処理もこちらで行う．
"""
import json
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from repo import Repo


def main():
    """
    最新コミットにおける製品コード群を取得し，
    それぞれについて定めた条件を満たしているかを確認する．
    その後，合格したものだけを統合していく．
    """
    result_dir = Path('../result') / Path(__file__).stem
    result_dir.mkdir(exist_ok=True, parents=True)

    target_list = [repo_prefix.glob('*').__next__().resolve()
                   for repo_prefix in Path('../repo').glob('*')]
    target_list.sort(key=lambda x: x.name)

    aggregated = {}
    aggregated_file_path = result_dir / 'aggregated.json'
    for target in tqdm(target_list):
        result = {}
        repo = Repo(target)
        repo_name = target.name
        result_file_path = result_dir / target.name / f'{target.name}.json'
        result_file_path.parent.mkdir(exist_ok=True)
        if result_file_path.exists():
            with result_file_path.open() as f:
                result = json.load(f)
                if result:
                    aggregated[repo.get_clone_url()] = result
            continue

        mapping_dict = get_mapping_dict(target.name)
        filter_prod_path(repo, mapping_dict)

        for prod_path, test_files in tqdm(list(mapping_dict.items()),
                                          leave=False):
            pynose_result, test_files \
                = get_pynose_result_for_product(repo_name, prod_path,
                                                mapping_dict, test_files)
            if not pynose_result:
                continue

            # 製品コード，テストコードそれぞれのメトリクスを取得する．

            store_result(result, prod_path, test_files, pynose_result)

        with result_file_path.open('w') as f:
            json.dump(result, f, indent=4)

        if result:
            aggregated[repo.get_clone_url()] = result

    with aggregated_file_path.open('w') as f:
        json.dump(aggregated, f, indent=4)


def get_mapping_dict(repo_name: str) -> dict:
    """
    mapping_prod_to_test.py の最新の結果から
    製品コードとそれをテストしているテストコードの一覧を取得する．
    :param repo_name: 結果が格納されているディレクトリの名前．
    """
    result_files = Path(f'../result/mapping_prod_to_test/{repo_name}').glob('*')
    latest_file = sorted(list(result_files), key=lambda x: x.name)[-1]
    with latest_file.open() as f:
        mapping_result = json.load(f)

    converted_result = {}
    for prod_path, test_path_list in mapping_result.items():
        converted_prod_path = Path(prod_path)
        converted_test_paths = [Path(test_path) for test_path in test_path_list]
        converted_result[converted_prod_path] = converted_test_paths
    return converted_result


def get_test_files(repo_name: str, bug_detected_commit: str,
                   mapping_dict: dict, prod_path: Path) -> list[Path]:
    """
    mapping_prod_to_test.py の結果から
    製品コードとそれをテストしているテストコードの一覧を取得する．
    もしもヒットしなければ間引く．
    :param repo_name: 結果が格納されているディレクトリの名前．
    :param bug_detected_commit: 検索対象のコミット．
    :param mapping_dict: 製品コードの辞書．
    :param prod_path: 製品コードのパス．
    """
    target_file = None
    result_files = Path(f'../result/mapping_prod_to_test/{repo_name}').glob('*')
    for result_file in result_files:
        if bug_detected_commit in result_file.as_posix():
            target_file = result_file
            break

    try:
        with target_file.open() as f:
            mapping_result = json.load(f)
        test_files = [Path(test_file)
                      for test_file in mapping_result[prod_path.as_posix()]]
        return test_files
    except AttributeError:
        del mapping_dict[prod_path]
        return []
    except KeyError:
        del mapping_dict[prod_path]
        return []


def filter_prod_path(repo: Repo, mapping_dict: dict):
    """
    以下の条件に従って製品コードを間引く．
    間引く条件を書いている．
    1.__init__.py ではない．
    2.変更履歴あり．
    :param repo: リポジトリを操作するクラス．
    :param mapping_dict: 製品コードの辞書．
    """
    for prod_path, _ in list(mapping_dict.items()):
        if prod_path.name == '__init__.py':
            del mapping_dict[prod_path]
            continue
        if repo.get_changed_times(file_path=prod_path) == 1:
            del mapping_dict[prod_path]


def get_pynose_result_for_product(repo_name: str, prod_path: Path,
                                  mapping_dict: dict, test_files: list[Path]):
    """
    指定された製品コードに対して、PyNose の解析結果を取得する．
    もしも過去にバグ修正が行われた履歴があれば，
      get_test_files と get_pynose_result を用いて対象コミットの結果を取得し，
      対象のテストコード群を更新する．
    バグ修正履歴が存在しない場合は，
      get_latest_pynose_result を用いて最新の解析結果を取得する．

    :param repo_name: 結果が格納されているディレクトリの名前．
    :param prod_path: 対象の製品コードのパス．
    :param mapping_dict: 製品コードと対応するテストコード群のマッピング辞書．
    :param test_files: 製品コードをテストしているテストコード群のパスのリスト．
    """
    bug_detected_commit = has_bug_history(repo_name, prod_path)
    if bug_detected_commit:
        test_files = get_test_files(repo_name, bug_detected_commit,
                                    mapping_dict, prod_path)
        pynose_result = get_pynose_result(prod_path, bug_detected_commit,
                                          repo_name, mapping_dict, test_files)
    else:
        pynose_result = get_latest_pynose_result(prod_path, repo_name,
                                                 mapping_dict, test_files)
    return pynose_result, test_files


def has_bug_history(repo_name: str, prod_path: Path) -> Optional[str]:
    """
    今までにバグ修正が行われたかを確認する．
    get_changed_files_before_merge.py によって出力された結果の各辞書の
    changed_files に prod_path があればバグ修正が行われている．
    そして，存在した場合は ベースコミットを返す．
    存在しなかった場合は何も返さない．
    なお，冒頭でヒットしてもさらにヒットした場合はそちらに更新する．
    :param repo_name: 結果が格納されているディレクトリの名前．
    :param prod_path: 製品コードのパス．
    """
    result_root = Path(f'../result/get_changed_files_before_merge')
    result_file_path = result_root / repo_name / f'{repo_name}.json'
    with result_file_path.open() as f:
        bug_fix_data_list = json.load(f)

    base_commit = None
    for bug_fix_data in bug_fix_data_list:
        if prod_path.as_posix() in bug_fix_data['changed_files']:
            base_commit = bug_fix_data['base_commit']

    return base_commit


def get_pynose_result(prod_path: Path, bug_detected_commit: str,
                      repo_name: str, mapping_dict: dict,
                      test_files: list[Path]):
    """
    指定されたコミットハッシュの PyNose の結果を取得する．
    ただし，対応するファイルが存在しないか prod_path に対応するものがなければ間引く．
    :param prod_path: 対象の製品コードのパス．
    :param bug_detected_commit: 検索対象のコミットハッシュ．
    :param repo_name: 結果が格納されているディレクトリの名前．
    :param mapping_dict: 製品コードの対応付けされた辞書．
    :param test_files: prod_path をテストしているコードのリスト．
    """
    if not test_files:
        return None

    target_file = None
    result_root = Path(f'../result/compress_pynose_result')
    result_files = Path(f'{result_root}/{repo_name}').glob('*')
    for result_file in result_files:
        if bug_detected_commit in result_file.as_posix():
            target_file = result_file
            break

    try:
        with target_file.open() as f:
            pynose_result = json.load(f)
        result = {}
        for test_file in test_files:
            smell_data = pynose_result[test_file.name]
            for smell, count in smell_data.items():
                result[smell] = result.get(smell, 0) + count
        return result
    except KeyError:
        del mapping_dict[prod_path]
    except AttributeError:
        del mapping_dict[prod_path]


def get_latest_pynose_result(prod_path: Path,
                             repo_name: str,
                             mapping_dict: dict,
                             test_files: list[Path]) -> dict:
    """
    最新の PyNose の結果を取得する．
    ただし， prod_path に対応するものがなければ間引く．
    :param prod_path: 対象の製品コードのパス．
    :param repo_name: 結果が格納されているディレクトリの名前．
    :param mapping_dict: 製品コードの対応付けされた辞書．
    :param test_files: prod_path をテストしているコードのリスト．
    """
    result_root = Path(f'../result/compress_pynose_result')
    result_files = Path(f'{result_root}/{repo_name}').glob('*')
    latest_file = sorted(list(result_files), key=lambda x: x.name)[-1]
    with latest_file.open() as f:
        pynose_result = json.load(f)

    try:
        result = {}
        for test_file in test_files:
            smell_data = pynose_result[test_file.name]
            for smell, count in smell_data.items():
                result[smell] = result.get(smell, 0) + count
        return result
    except KeyError:
        del mapping_dict[prod_path]


def store_result(result: dict, prod_path: Path,
                 test_files: list, pynose_result: dict):
    """
    結果を格納する．
    :param result: 結果を格納する辞書．
    :param prod_path: 製品コードのパス．
    :param test_files: 製品コードをテストするテストファイル群のパス．
    :param pynose_result: pynose の結果．
    """
    result[prod_path.as_posix()] = {'test_files': [test_file.as_posix()
                                                   for test_file in test_files],
                                    'pynose_result': pynose_result}


if __name__ == '__main__':
    main()
