"""
バグに関する issue が閉じられるまでに変更のあったファイルパスを取得する．
ただし，マージコミットの親が 3 つ以上の場合は何も取得しない．
"""
import json
from pathlib import Path

from tqdm import tqdm

from repo import Repo


def main():
    """
    コミットメッセージとバグに関する issue 番号を用いてマージコミットを特定する．
    その後，その issue が閉じられるまでに変更のあったファイルパスを取得する．
    """
    result_dir = Path('../result') / Path(__file__).stem
    result_dir.mkdir(exist_ok=True, parents=True)

    target_list = [repo_prefix.glob('*').__next__().resolve()
                   for repo_prefix in Path('../repo').glob('*')]
    target_list.sort(key=lambda x: x.name)

    aggregated = {}
    aggregated_file_path = result_dir / 'aggregated.json'
    for target in tqdm(target_list):
        result = []
        result_file_path = result_dir / target.name / f'{target.name}.json'
        result_file_path.parent.mkdir(exist_ok=True)
        if result_file_path.exists():
            with result_file_path.open() as f:
                aggregated[target.name] = json.load(f)
            continue

        repo = Repo(target)
        merge_commit_list = identify_merge_commits(target.name)
        for merge_commit in tqdm(merge_commit_list, leave=False):
            parents = repo.get_parents(merge_commit)
            if len(parents) == 2:
                base_commit = repo.get_base_commit_hash(merge_commit)
                changed_files = get_changed_files(repo, merge_commit)
                store_result(result, merge_commit, base_commit, changed_files)

        with result_file_path.open('w') as f:
            json.dump(result, f, indent=4)

        aggregated[target.name] = result

    with aggregated_file_path.open('w') as f:
        json.dump(aggregated, f, indent=4)


def identify_merge_commits(repo_name: str) -> list:
    """
    コミットメッセージとバグに関する issue 番号を用いてマージコミットを特定する．
    :param repo_name: 結果が格納されているディレクトリの名前．
    """
    merge_commits = []

    bug_issue_numbers = get_bug_issue_numbers(repo_name)
    commit_messages = get_commit_messages(repo_name)

    for bug_issue_number in bug_issue_numbers:
        for commit_hash, commit_message in commit_messages.items():
            if f'#{bug_issue_number}' in commit_message:
                merge_commits.append(commit_hash)
    return merge_commits


def get_bug_issue_numbers(repo_name: str) -> list:
    """
    取得してあるバグに関する issue 番号を読み込む．
    :param repo_name: 結果が格納されているディレクトリの名前．
    """
    result_root = Path(f'../result/fetch_bug_issue_numbers')
    file_path = result_root / repo_name / f'{repo_name}.json'
    with file_path.open() as f:
        return json.load(f)


def get_commit_messages(repo_name) -> dict:
    """
    取得してあるコミットメッセージを読み込む．
    :param repo_name: 結果が格納されているディレクトリの名前．
    """
    result_root = Path(f'../result/get_commit_messages')
    file_path = result_root / repo_name / f'{repo_name}.json'
    with file_path.open() as f:
        return json.load(f)


def get_changed_files(repo: Repo, merge_commit: str) -> list:
    """
    マージコミットによって issue が閉じられるまでに変更のあったファイルパスを取得する．
    ただし， issue に関連しないファイルパスは取得しない．
    :param repo: リポジトリを操作するクラス．
    :param merge_commit: マージコミットだと判断されたコミット．
    """
    changed_files = repo.get_changed_files(merge_commit)
    return changed_files


def store_result(result: list, merge_commit: str,
                 base_commit: str, changed_files: list):
    """
    結果を格納する．
    :param result: 結果を格納する配列．
    :param merge_commit: マージコミットだと判定されたコミット．
    :param base_commit: ブランチが分岐する前のコミット．
    :param changed_files: issue が閉じられるまでに修正されたファイル群のパス．
    """
    integrated_result = {'merge_commit': merge_commit,
                         'base_commit': base_commit,
                         'changed_files': changed_files}
    result.append(integrated_result)


if __name__ == '__main__':
    main()
