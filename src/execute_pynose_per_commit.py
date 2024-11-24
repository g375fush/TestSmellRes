"""
PyNose をコミットごとに実行するプログラム．
"""
import json
import shutil
import sys
import time
from pathlib import Path

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
        error_recorded_file_path = result_dir / f'{repo_name}_error.json'
        for index, commit_hash in enumerate(commit_hashes, 1):
            result_file_name = f'{repo_name}_{index:06d}_{commit_hash}.json'
            log_file_name = f'{repo_name}_{index:06d}_{commit_hash}.txt'

            result_file_path = result_dir / result_file_name
            log_file_path = result_dir / log_file_name
            if already_analyzed(result_file_path):
                print(f'skip {commit_hash}')
                continue

            if error_commit_hash(error_recorded_file_path, commit_hash):
                print(f'skip {commit_hash} due to some error')
                continue

            repo.checkout(commit_hash)

            try:
                pynose_executor.execute_pynose()
            except KeyboardInterrupt:
                remove_pynose_dir(pynose_instance_path)
                sys.exit(0)
            except TimeoutError:
                record_error_commit_hash(commit_hash, 'Timeout',
                                         error_recorded_file_path)
                continue
            finally:
                print(f'{repo_name} {index}/{len(commit_hashes)}')

            try:
                default_result_file_path.rename(result_file_path)
                default_log_file_path.unlink()
            except FileNotFoundError:
                print('PyNose did not output result file')
                record_error_commit_hash(commit_hash, 'OnlyLogFile',
                                         error_recorded_file_path)
                try:
                    default_log_file_path.rename(log_file_path)
                except FileNotFoundError:
                    print('PyNose did not output log file')

        if pynose_instance_path.exists():
            shutil.rmtree(pynose_instance_path)


def already_analyzed(file_path: Path):
    """
    すでにファイルが存在しているならば解析済みである．
    :param file_path: 結果のファイルパス．
    :return: file_path が存在しているかどうか．
    """
    return file_path.exists()


def remove_pynose_dir(dir_path: Path):
    """
    PyNose を削除しようと試みる．
    :param dir_path: PyNose へのパス．
    """
    try:
        shutil.rmtree(dir_path)
    except FileNotFoundError:
        time.sleep(3)
        shutil.rmtree(dir_path)
    except OSError:
        time.sleep(3)
        shutil.rmtree(dir_path)


def record_error_commit_hash(commit_hash: str, reason: str, path: Path):
    """
    解析時にエラーとなったコミットハッシュを記録する．
    :param commit_hash: コミットハッシュ．
    :param reason: エラーと判断した理由．
    :param path: 記録するファイルのパス．
    """
    if not path.exists():
        error_dict = {}
    else:
        with path.open() as f:
            error_dict = json.load(f)

    error_dict[commit_hash] = reason
    with path.open('w') as f:
        json.dump(error_dict, f, indent=4)


def error_commit_hash(path: Path, commit_hash: str):
    """
    前回の解析でエラーと判断されたコミットハッシュ群に，
    与えられたコミットハッシュが含まれているかを判定する．
    :param path: エラーが記録されているファイルのパス．
    :param commit_hash: 判定するコミットハッシュ．
    """
    if not path.exists():
        return False

    with path.open() as f:
        errors = f.read()
    return True if commit_hash in errors else False


if __name__ == '__main__':
    main()
