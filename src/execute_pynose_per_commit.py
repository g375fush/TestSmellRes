"""
PyNose をコミットごとに実行するプログラム．
"""
from pathlib import Path

from global_var import deadline, runner_path
from pynose_executor import PyNoseExecutor
from repo import Repo


def main():
    """
    リポジトリのコミットごとに PyNose を実行する．
    ただし，あらかじめクローンされているリポジトリを対象とする．
    """
    this_file_name = Path(__file__).stem
    target_list = list(Path('../repo').resolve(strict=True).glob('*'))
    target_list.sort()
    for repo_prefix in target_list:
        result_dir = Path(f'../result/{this_file_name}/{repo_prefix}')
        result_dir.mkdir(exist_ok=True, parents=True)
        pynose_executor = PyNoseExecutor(runner_path=runner_path,
                                         result_dir=result_dir,
                                         repo_prefix=repo_prefix)

        repo_name = repo_prefix.glob('*').__next__()
        repo_path = repo_prefix / repo_name
        repo = Repo(repo_path)

        commit_hashes = repo.get_commit_hashes(until=deadline)
        for index, commit_hash in enumerate(commit_hashes, 1):
            repo.checkout(commit_hash)
            pynose_executor.execute_pynose()
            default_file_name = f'{repo_name}.json'
            result_file_name = f'{repo_name}_{index:06d}_{commit_hash}.json'
            result_dir.joinpath(default_file_name).rename(result_file_name)

        result_dir.joinpath('log.txt').unlink()


if __name__ == '__main__':
    main()
