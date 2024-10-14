from tinydb import TinyDB, Query

db = TinyDB('comments.json')

Comment = Query()


def has_already_commented(repo_name, pr_number):
    return db.contains((Comment.repo_name == repo_name) & (Comment.pr_number == pr_number))


def insert_comment_record(repo_name, pr_number):
    comment_record = {"repo_name": repo_name, "pr_number": pr_number}
    db.insert(comment_record)
