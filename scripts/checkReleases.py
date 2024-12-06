import sys
import os
import json
import requests
from typing import List

STATE_FILE = "release_state.json"

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from dotenv import load_dotenv
# from utils.qywechat_notify import send_wechat_notification
# from utils.qmsg_notify import send_qmsg_notification
from utils.serve_chan_notify import send_server_chan_notification

# 仅在本地环境中加载 .env 文件
if os.getenv("GITHUB_ACTIONS") is None:  # GITHUB_ACTIONS 在 GitHub Actions 环境中会自动设置为 "true"
    load_dotenv()

def load_state(state_file: str) -> dict:
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state_file: str, state: dict):
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def get_all_releases(repo: str, token: str = None) -> list:
    owner, repo_name = repo.split("/")
    url = f"https://api.github.com/repos/{owner}/{repo_name}/releases"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Release-Checker",
    }
    if token:
        headers["Authorization"] = f"token {token}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"无法获取仓库 {repo} 的发布信息。状态码：{response.status_code}")
        return None

def get_latest_release(repo: str, token: str = None) -> dict:
    releases = get_all_releases(repo, token)
    if not releases:
        return None
    # 最新的发布通常是列表中的第一个元素
    return releases[0] if releases else None

def parse_repos(repos_env: str) -> List[str]:
    repos = [repo.strip() for repo in repos_env.split(",") if repo.strip()]
    return repos

def main():
    state = load_state(STATE_FILE)
    token = os.getenv("REPOS_TOKEN")
    repos_env = os.getenv("REPOS", "")
    webhook_url = os.getenv('WEBHOOK_URL')
    repos = parse_repos(repos_env)
    notify_messages: List[str] = []

    if not repos:
        print("没有定义要监控的仓库（REPOS 环境变量为空）。")
        return

    for repo in repos:
        if '/' not in repo:
            print(f"仓库名称格式错误（应为 owner/repo）：{repo}")
            continue
        release = get_latest_release(repo, token)
        if not release:
            continue

        tag = release.get("tag_name")
        html_url = release.get("html_url")
        if not tag or not html_url:
            continue

        previous_tag = state.get(repo)
        if previous_tag != tag:
            notify_messages.append(f"- **[{repo}](https://github.com/{repo})** 有新的发布：`{tag}`\n  [查看发布详情]({html_url})")
            state[repo] = tag  # 更新状态

    save_state(STATE_FILE, state)

    if notify_messages:
        notify_content = "\n".join(notify_messages)
        print(notify_content)
        
        # 使用 Server酱发送通知
        send_server_chan_notification('Check Github Release', notify_content)

        with open(os.getenv('GITHUB_OUTPUT'), 'a') as f:
            f.write("notify=New\n")
    else:
        print("今天没检测到关注的Github仓库有新发布！")

        # 使用 Server酱发送通知
        send_server_chan_notification('Check Github Release', "今天没检测到关注的Github仓库有新发布！")

if __name__ == "__main__":
    main()
    
