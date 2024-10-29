"""
リポジトリを扱うクラス．
"""
from datetime import datetime
from pathlib import Path
from typing import Optional

import git


class Repo:
    """
    checkout などの git に関する処理を担当するクラス．
    """

    def __init__(self, repo_path: Path):
        self._repo = git.Repo(repo_path.as_posix())

    def get_commit_hashes(self, until: Optional[datetime] = None) -> list:
        """
        コミットハッシュを取得する．

        :param until: どの時点までのコミットハッシュを取得するか．デフォルトは最新まで．
        :return: コミットハッシュのリスト．
        """
        commits = self._repo.iter_commits(reverse=True, until=until)
        return [commit.hexsha for commit in commits]

    def get_commit_messages(self, until: Optional[datetime] = None) -> list:
        """
        コミットメッセージを取得する．

        :param until: どの時点までのコミットメッセージを取得するか．デフォルトは最新まで．
        :return: コミットメッセージのリスト．
        """
        commits = self._repo.iter_commits(reverse=True, until=until)
        return [commit.message for commit in commits]

    def checkout(self, commit_hash: str) -> None:
        """
        指定したコミットハッシュにチェックアウトする．

        :param commit_hash: チェックアウト対象のコミットハッシュ．

        :return:
        """
        print(f'start checkout {commit_hash}')
        try:
            self._repo.git.checkout(commit_hash, force=True)
        except git.exc.GitCommandError:
            print('Failed to checkout')
            raise
        print(f'finish checkout {commit_hash}')

    def checkout_head_commit(self):
        """
        HEAD コミットにチェックアウトする．

        :return:
        """
        try:
            self._repo.git.checkout(self._repo.remotes.origin.refs.HEAD.commit)
        except git.exc.GitCommandError:
            print('Failed to checkout')
            raise
