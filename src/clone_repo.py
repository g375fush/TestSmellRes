"""
リポジトリをすべてクローンする．
"""
import os
from pathlib import Path
from subprocess import run

import git

from global_var import deadline
from repo import Repo


def main():
    """
    url_list から対象リポジトリの url を取得し，
    それらをクローンする．
    """
    urls = get_urls()
    for index, url in enumerate(urls, start=1):
        repo_prefix = Path(f'../repo/[{index:04d}]').resolve()
        clone(url, repo_prefix)


def get_urls():
    """
    対象となる url を取得する．
    :return urls: 対象となる url 群．
    """
    with open('../url_list/dataset_primary.txt', encoding='utf-8') as f:
        urls = f.read().splitlines()
    return urls


def clone(url: str, repo_prefix: Path):
    """
    リポジトリをクローンする．
    もしすでに存在する場合は一番古いコミットハッシュと対象最新コミットに
    チェックアウトできるか調査してできるならばスキップ．
    できなければ削除する．
    :param url: クローン用の url．
    :param repo_prefix: リポジトリのディレクトリを格納するディレクトリのパス．
    """
    repo_name = url.split('/')[-1].replace('.git', '')
    clone_name = repo_prefix.name + repo_name
    clone_path = repo_prefix.joinpath(clone_name).resolve()

    if clone_path.exists():
        if available_repo(clone_path):
            print(f'{clone_name} is available')
            return
        else:
            print(f'{clone_name} is not available')
            delete_repo(repo_prefix, clone_name)

    print(f'Cloning {clone_name} ...')
    try:
        git.Repo.clone_from(url=url, to_path=clone_path)
    except git.GitCommandError as e:
        print(f'failed to clone {clone_name} ...')
        print(f'due to: {e.stderr}')
        delete_repo(repo_prefix, clone_name)
    else:
        print(f'Cloned {clone_name} !!!')


def available_repo(repo_path: Path):
    """
    使用可能なリポジトリかを確認する．
    :param repo_path: リポジトリへのパス．
    """
    try:
        repo = Repo(repo_path)
    except IndexError:
        return False

    commit_hashes = repo.get_commit_hashes(until=deadline)
    oldest_commit_hash = commit_hashes[0]
    try:
        repo.checkout(oldest_commit_hash)
        return True
    except git.GitCommandError:
        return False


def delete_repo(repo_prefix: Path, clone_name: str):
    """
    リポジトリを削除する．
    :param repo_prefix: リポジトリの親ディレクトリ．
    :param clone_name: クローン時の名前．
    """
    print(f'deleting {clone_name} ...')
    if os.name == 'nt':
        run(['rmdir', '/S', '/Q', str(repo_prefix)], shell=True)
    else:
        run(['rm', '-rf', repo_prefix.as_posix()])
    print(f'deleted {clone_name} !!!')


if __name__ == '__main__':
    main()
