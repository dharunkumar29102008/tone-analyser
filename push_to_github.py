import sys
import os
import dulwich.porcelain as git

def push_repo(token=None):
    token = token or os.getenv("GITHUB_TOKEN")
    if not token and len(sys.argv) > 1:
        token = sys.argv[1].strip()

    if not token:
        print("\n[!] Please provide your GitHub Personal Access Token (PAT).")
        print("Usage: python push_to_github.py <YOUR_GITHUB_TOKEN>\n")
        print("To create a token: GitHub -> Settings -> Developer Settings -> Personal Access Tokens -> Tokens (classic) -> check 'repo'.\n")
        sys.exit(1)

    repo_url = f"https://{token}@github.com/dharunkumar29102008/tone-analyser.git"
    print(f"[*] Pushing 'main' branch to https://github.com/dharunkumar29102008/tone-analyser.git ...")
    try:
        git.push('.', repo_url, 'refs/heads/main')
        print("[+] Successfully pushed all code to GitHub!")
    except Exception as e:
        print(f"[!] Push failed: {e}")

if __name__ == "__main__":
    push_repo()
