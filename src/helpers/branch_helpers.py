import subprocess

def get_default_branch(gitops_repository_with_pat):
    result = subprocess.run(["git", "ls-remote", "--symref", gitops_repository_with_pat, "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

    for line in result.stdout.splitlines():
        if line.startswith("ref:"):
            default_branch = line.split("refs/heads/")[1].split()[0]
            return default_branch
    
    return None