"""
PyNose の解析の進捗を表示するプログラム．
"""
from pathlib import Path

from tqdm import tqdm

from global_var import deadline
from repo import Repo


def main():
    """
    PyNose の解析の進捗を表示する．
    ただし，エラーファイルが存在する場合は読み込み，進捗に取り入れる．
    """
    repo_list = list(Path('../repo').resolve(strict=True).glob('*'))
    repo_list.sort()
    for repo_prefix in tqdm(repo_list):
        try:
            repo_name = repo_prefix.glob('*').__next__().stem
        except StopIteration:
            tqdm.write(f'skip {repo_prefix}')
            continue

        repo_path = repo_prefix / repo_name
        repo = Repo(repo_path)

        result_dir \
            = Path(f'../result/execute_pynose_per_commit/{repo_name}').resolve()
        errors = get_errors(result_dir)
        commit_hashes = repo.get_commit_hashes(until=deadline)
        analyzed = 0
        total = 0
        for index, commit_hash in enumerate(commit_hashes, 1):
            result_file_name = f'{repo_name}_{index:06d}_{commit_hash}.json'
            result_file_path = result_dir / result_file_name

            if result_file_path.exists() or (commit_hash in errors):
                analyzed += 1
            total += 1

        if analyzed != total:
            tqdm.write(f'{repo_prefix.stem}: {analyzed*100/total:>6.2f}% '
                       f'{analyzed:>6d} {total:>6d}')


def get_errors(path: Path):
    """
    エラーファイルが存在する場合はその内容を返す．
    存在しない場合は空文字を返す．
    :param path: エラーファイルが存在すれば格納されているディレクトリのパス．
    """
    error_file_path = path.glob('*error*').__next__()
    if not error_file_path.exists():
        return ''

    with error_file_path.open() as f:
        return f.read()


if __name__ == '__main__':
    main()
