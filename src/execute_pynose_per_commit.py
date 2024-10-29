"""
PyNose をコミットごとに実行するプログラム．
"""
import shutil
import sys
import time
from pathlib import Path

import git.exc

from global_var import deadline, runner_path
from pynose_executor import PyNoseExecutor
from repo import Repo


def main():
    """
    リポジトリのコミットごとに PyNose を実行する．
    ただし，あらかじめクローンされているリポジトリを対象とする．
    """
    start = int(input('start:'))
    end = int(input('end:'))

    this_file_name = Path(__file__).stem
    target_list = list(Path('../repo').resolve(strict=True).glob('*'))
    target_list.sort()
    for repo_prefix in target_list:
        prefix_number = int(repo_prefix.stem[1:5])
        if not start <= prefix_number <= end:
            continue

        pynose_instance_path = Path(f'../{repo_prefix.stem}_PyNose').resolve()
        if pynose_instance_path.exists():
            shutil.rmtree(pynose_instance_path)
        shutil.copytree(runner_path.parent, pynose_instance_path)

        try:
            repo_name = repo_prefix.glob('*').__next__().stem
        except StopIteration:
            shutil.rmtree(pynose_instance_path)
            continue
        repo_path = repo_prefix / repo_name
        repo = Repo(repo_path)

        try:
            repo.checkout_head_commit()
        except git.exc.GitCommandError:
            continue

        result_dir \
            = Path(f'../result/{this_file_name}/{repo_name}').resolve()
        result_dir.mkdir(exist_ok=True, parents=True)
        pynose_executor = PyNoseExecutor(
            runner_path=pynose_instance_path / 'runner.py',
            result_dir=result_dir,
            repo_prefix=repo_prefix
        )

        commit_hashes = repo.get_commit_hashes(until=deadline)
        default_result_file_path = result_dir / f'{repo_name}.json'
        default_log_file_path = result_dir / 'log.txt'
        for index, commit_hash in enumerate(commit_hashes, 1):
            result_file_name = f'{repo_name}_{index:06d}_{commit_hash}.json'
            log_file_name = f'{repo_name}_{index:06d}_{commit_hash}.txt'

            result_file_path = result_dir / result_file_name
            log_file_path = result_dir / log_file_name
            if already_analyzed(result_file_path):
                print(f'skip {commit_hash}')
                continue

            repo.checkout(commit_hash)

            try:
                pynose_executor.execute_pynose()
            except KeyboardInterrupt:
                try:
                    shutil.rmtree(pynose_instance_path)
                except FileNotFoundError:
                    time.sleep(1)
                    shutil.rmtree(pynose_instance_path)
                except OSError:
                    time.sleep(1)
                    shutil.rmtree(pynose_instance_path)
                    sys.exit(0)
            else:
                print(f'{repo_name} {index}/{len(commit_hashes)}')

            default_result_file_path.rename(result_file_path)
            default_log_file_path.rename(log_file_path)

        if pynose_instance_path.exists():
            shutil.rmtree(pynose_instance_path)


def already_analyzed(file_path: Path):
    """
    すでにファイルが存在しているならば解析済みである．
    :param file_path: 結果のファイルパス．
    :return: file_path が存在しているかどうか．
    """
    return file_path.exists()


if __name__ == '__main__':
    main()
