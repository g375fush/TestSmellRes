"""
1 つのプロジェクトを分割して解析する．
端末を分離し，そこで実行する．
ただし，プロジェクト初期と最新ではファイル数に差があるため，
剰余を使って均等にタスクを割り当てる．
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

from global_var import runner_path
from repo import Repo
from pynose_executor import PyNoseExecutor


def main():
    """
    タブを開くコマンドである gnome-terminal --tab を使用してタブを開く．
    そして， -- bash -c "【command】; exec bash" を使用して新しいタブでコマンドを実行する．
    """
    args = sys.argv
    main_process = len(args) == 1
    if main_process:
        allocate_task()
    else:
        exe_pynose(args)


def allocate_task():
    """
    ユーザーが入力した分割数に応じてタスクを振り分ける．
    """
    this_file_name = Path(__file__).name
    repo_prefix = f'[{int(input("repo_number:")):04d}]'
    repo_path = Path(f'../repo/{repo_prefix}').resolve().glob('*').__next__()
    div = int(input('div:'))
    for i in range(div):
        python_cmd = f'python {this_file_name} {repo_path.as_posix()} {i} {div}'
        cmd = f'gnome-terminal --tab -- bash -c "{python_cmd}; exec bash"'
        subprocess.Popen(cmd, shell=True)


def exe_pynose(args: list):
    """
    PyNose を実行する．
    """
    r = int(args[2])
    div = int(args[3])

    # リポジトリ PyNose のコピーをとる．
    original_repo_path = Path(args[1])
    repo_name = original_repo_path.name
    repo_path = Path(f'../{repo_name}_{r:02d}/{repo_name}_{r:02d}').resolve()
    if repo_path.exists():
        shutil.rmtree(repo_path.parent)
    shutil.copytree(original_repo_path, repo_path)

    original_pynose_path = runner_path.parent
    pynose_path = Path(f'../{repo_name}_{r:02d}_PyNose').resolve()
    if pynose_path.exists():
        shutil.rmtree(pynose_path)
    shutil.copytree(original_pynose_path, pynose_path)

    # コミットハッシュごとに解析するならば解析する．
    result_dir = Path(
        f'../result/execute_pynose_per_commit/{repo_name}').resolve()
    result_dir.mkdir(exist_ok=True)
    repo = Repo(repo_path)
    executor = PyNoseExecutor(runner_path=pynose_path / 'runner.py',
                              result_dir=result_dir,
                              repo_prefix=repo_path.parent)
    error_recorded_file_path = result_dir / f'{repo_name}_error.json'
    default_result_file_path = result_dir / f'{repo_name}_{r:02d}.json'
    default_log_file_path = result_dir / 'log.txt'
    commit_hashes = repo.get_commit_hashes()
    for index, commit_hash in enumerate(commit_hashes):
        if index % div != r:
            continue

        result_file = f'{repo_name}_{index + 1:06d}_{commit_hash}.json'
        result_file_path = result_dir / result_file
        log_file_name = f'{repo_name}_{index:06d}_{commit_hash}.txt'
        log_file_path = result_dir / log_file_name

        if result_file_path.exists():
            continue

        if error_commit_hash(error_recorded_file_path, commit_hash):
            print(f'skip {commit_hash} due to some error')
            continue

        repo.checkout(commit_hash)
        try:
            executor.execute_pynose()
        except KeyboardInterrupt:
            shutil.rmtree(repo_path.parent)
            shutil.rmtree(pynose_path)
            sys.exit(0)
        except TimeoutError:
            record_error_commit_hash(commit_hash, 'Timeout',
                                     error_recorded_file_path)
            continue
        finally:
            print(f'{repo_name} {index}/{len(commit_hashes)}')

        default_log_file_path.unlink(missing_ok=True)
        try:
            default_result_file_path.rename(result_file_path)
        except FileNotFoundError:
            print('PyNose did not output result file')
            record_error_commit_hash(commit_hash, 'OnlyLogFile',
                                     error_recorded_file_path)
            try:
                default_log_file_path.rename(log_file_path)
            except FileNotFoundError:
                print('PyNose did not output log file')

    # 削除する．
    shutil.rmtree(repo_path.parent)
    shutil.rmtree(pynose_path)


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
        f.write("\n")


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
