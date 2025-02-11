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
        self.repo_path = repo_path
        self._repo = git.Repo(repo_path.as_posix())
        self.branch_name = self._repo.branches[0] # noqa
        self.name: str = repo_path.name

    def get_commit_hashes(self, until: Optional[datetime] = None) -> list:
        """
        コミットハッシュを取得する．

        :param until: どの時点までのコミットハッシュを取得するか．デフォルトは最新まで．
        :return: コミットハッシュのリスト．
        """
        commits = self._repo.iter_commits(self.branch_name,
                                          reverse=True,
                                          until=until)
        return [commit.hexsha for commit in commits]

    def get_commit_messages(self, until: Optional[datetime] = None) -> list:
        """
        コミットメッセージを取得する．

        :param until: どの時点までのコミットメッセージを取得するか．デフォルトは最新まで．
        :return: コミットメッセージのリスト．
        """
        commits = self._repo.iter_commits(self.branch_name,
                                          reverse=True,
                                          until=until)
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

    def get_clone_url(self) -> str:
        """
        clone 用の url を取得する．
        :return: clone 用の url．
        """
        return self._repo.remotes.origin.url

    def get_parents(self, commit_hash: str) -> list:
        """
        与えられたコミットハッシュの親が 2 つであるかを判定する．
        """
        commit = self._repo.commit(commit_hash)
        return list(commit.parents)

    def get_base_commit_hash(self, commit_hash: str) -> Optional[str]:
        """
        マージコミットの親同士の共通祖先のコミットハッシュを返す.
        マージコミットでない場合や見つからなかった場合は None を返す.
        ベースコミットがメインブランチに存在しない場合も None を返す．
        """
        merge_commit = self._repo.commit(commit_hash)
        base_commit = self._repo.merge_base(*merge_commit.parents)
        return base_commit[0].hexsha if base_commit else None

    def get_changed_files(self, commit_hash: str) -> list:
        """
        そのコミットで変更のあったファイルを取得する．
        """
        changed_files = []
        option = ['-m', '--pretty=format:', '--name-only']
        git_output = self._repo.git.show(*option, commit_hash)
        for file_path in git_output.splitlines():
            if file_path:
                changed_files.append(file_path)
        return changed_files
