"""
対象となったリポジトリのコミットハッシュを製品コードのパスをキーとして出力する．
出力するコミットハッシュの種類は以下の 3 つ．
１．最新コミットと定義したコミットハッシュ．
２．マージコミットと判断したコミットハッシュ．
３．２ で判断したコミットのベースコミットハッシュ．
"""
import json
from pathlib import Path

from tqdm import tqdm


def main():
    """
    data_forge.py から対象となる製品コードの一覧を取得し，
    get_changed_files_before_merge.py からマージ関連のコミットハッシュを取得する．
    """
    result_dir = Path('../result') / Path(__file__).stem
    result_dir.mkdir(exist_ok=True, parents=True)

    data_forged_json = load_data_forged_json()

    aggregated = {}
    aggregated_file_path = result_dir / 'aggregated.json'
    for url, prod_data_dict in tqdm(list(data_forged_json.items())):
        repo_name, latest_commit_hash = get_latest_commit_hash(url)

        result = {}
        result_file_path = result_dir / repo_name / f'{repo_name}.json'
        result_file_path.parent.mkdir(exist_ok=True)
        for prod_path, prod_data in prod_data_dict.items():
            if prod_data['bug']:
                merge_commit, base_commit \
                    = get_merge_and_base_commit_hash(repo_name, prod_path)
                result[prod_path] = {'merge_commit': merge_commit,
                                     'base_commit': base_commit}
            else:
                result[prod_path] = {'latest_commit_hash': latest_commit_hash}

        with result_file_path.open('w') as f:
            json.dump(result, f, indent=4)

        aggregated[url] = result

    with aggregated_file_path.open('w') as f:
        json.dump(aggregated, f, indent=4)


def load_data_forged_json() -> dict:
    """
    data_forge.py のデータを読み込む．
    """
    with Path('../result/data_forge/aggregated.json').open() as f:
        return json.load(f)


def get_merge_and_base_commit_hash(repo_name: str, prod_path: str) -> tuple:
    """
    get_changed_files_before_merge.py からマージ関連のコミットハッシュを取得する．
    """
    result_root = Path('../result/get_changed_files_before_merge')
    file_path = result_root / repo_name / f'{repo_name}.json'
    with file_path.open() as f:
        bug_fix_data_list = json.load(f)

    merge_commit = None
    base_commit = None
    for bug_fix_data in bug_fix_data_list:
        if prod_path in bug_fix_data['changed_files']:
            merge_commit = bug_fix_data['merge_commit']
            base_commit = bug_fix_data['base_commit']

    return merge_commit, base_commit


def get_latest_commit_hash(url: str) -> tuple[str, str]:
    """
    url からリポジトリの名前を取得して対応するファイルを特定し，
    最新と定義したコミットハッシュを取得する．
    """
    repo_name = get_repo_name(url)
    file_path = Path(f'../result/dump_commit_hash/{repo_name}.json')
    with file_path.open() as f:
        commit_hashes = json.load(f)
    return file_path.stem, commit_hashes[-1]


def get_repo_name(target_url: str):
    """
    url_list から url を取得して番号をつけてリポジトリ名を返す．
    """
    with open('../url_list/dataset_primary.txt', encoding='utf-8') as f:
        urls = f.read().splitlines()

    for index, url in enumerate(urls, start=1):
        if url == target_url:
            return f'[{index:04d}]{url.rsplit("/")[-1].replace(".git", "")}'


if __name__ == '__main__':
    main()
