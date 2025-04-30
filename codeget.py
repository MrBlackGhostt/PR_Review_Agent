from github import Github
import re
import json


def extract_pr_changes(access_token, repo_owner, repo_name, pr_number=None):
    """
    Extract code changes from GitHub pull requests.

    Args:
        access_token (str): GitHub personal access token
        repo_owner (str): Repository owner
        repo_name (str): Repository name
        pr_number (int, optional): Specific PR number to analyze. If None, analyze all open PRs.

    Returns:
        dict: JSON-formatted data containing code changes
    """
    # Initialize GitHub client
    g = Github(access_token)

    # Get repository
    repo = g.get_repo(f"{repo_owner}/{repo_name}")

    results = []

    # Get pull requests to analyze
    if pr_number:
        pull_requests = [repo.get_pull(pr_number)]
    else:
        pull_requests = repo.get_pulls(state="open")

    for pull_request in pull_requests:
        pr_data = {
            "pr_number": pull_request.number,
            "pr_title": pull_request.title,
            "pr_author": pull_request.user.login,
            "pr_description": pull_request.body,
            "pr_commit_message": pull_request.title,  # Using title as commit message for simplicity
            "file_changes": [],
        }

        # Get commit messages
        commits = pull_request.get_commits()
        commit_messages = [commit.commit.message for commit in commits]
        pr_data["commit_messages"] = commit_messages

        # Process each file
        files = pull_request.get_files()
        for file in files:
            file_data = {
                "file_path": file.filename,
                "status": file.status,
                "original_code": {},
                "modified_code": {},
            }

            # Skip binary files
            if file.patch is None:
                file_data["note"] = "Binary file or too large to display"
                pr_data["file_changes"].append(file_data)
                continue

            # Parse the patch
            hunks = parse_patch(file.patch)

            for hunk_index, hunk in enumerate(hunks):
                hunk_id = f"hunk_{hunk_index+1}"
                file_data["original_code"][hunk_id] = hunk["removed"]
                file_data["modified_code"][hunk_id] = hunk["added"]

            pr_data["file_changes"].append(file_data)

        results.append(pr_data)

    # Return results as a dictionary that can be easily converted to JSON
    if pr_number:
        return results[0]  # Return just the single PR data
    return {"pull_requests": results}


def parse_patch(patch):
    """
    Parse a git patch into hunks of added and removed code.

    Args:
        patch (str): The patch content from GitHub API

    Returns:
        list: List of dictionaries, each representing a hunk with added and removed code
    """
    if not patch:
        return []

    # Split the patch into hunks (sections starting with @@)
    hunk_pattern = r"@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@.*?(?=(?:\n@@ |\Z))"
    hunks_raw = re.findall(hunk_pattern, patch, re.DOTALL)

    parsed_hunks = []
    for hunk_raw in hunks_raw:
        lines = hunk_raw.split("\n")

        # Skip the @@ line
        content_lines = lines[1:]

        removed_lines = []
        added_lines = []

        for line in content_lines:
            if not line:
                continue

            if line.startswith("-"):
                removed_lines.append(line[1:])
            elif line.startswith("+"):
                added_lines.append(line[1:])
            # Context lines are ignored for clarity

        parsed_hunks.append(
            {"removed": "\n".join(removed_lines), "added": "\n".join(added_lines)}
        )

    return parsed_hunks


def generate_pr_review(pr_data):
    """
    Generate a structured review of the pull request.

    Args:
        pr_data (dict): Pull request data from extract_pr_changes

    Returns:
        dict: JSON-formatted review data
    """
    review = {"file_changes": [], "need_update": [], "comment": ""}

    # Process file changes
    for file_change in pr_data["file_changes"]:
        file_path = file_change["file_path"]

        # Create a summary of changes
        changes_summary = f"Modified file with {len(file_change['original_code'])} code sections changed"
        if file_change["status"] == "added":
            changes_summary = "New file added to the repository"
        elif file_change["status"] == "removed":
            changes_summary = "File removed from the repository"

        review["file_changes"].append(
            {"file_path": file_path, "changes": changes_summary}
        )

        # This is where you would add code analysis logic
        # For now, we'll just add placeholder analysis for demonstration

        # Check if file has changes that might need updates
        if file_change["status"] != "removed" and len(file_change["modified_code"]) > 0:
            # Example analysis (replace with actual analysis logic)
            issues = []
            suggestions = []

            # Add file to need_update if we found issues
            if issues:
                update_data = {
                    "file_path": file_path,
                    "issues": issues,
                    "suggestions": suggestions,
                }

                # Add code examples
                for hunk_id, original in file_change["original_code"].items():
                    if hunk_id in file_change["modified_code"]:
                        update_data["current_code"] = file_change["modified_code"][
                            hunk_id
                        ]
                        update_data["suggested_code"] = file_change["modified_code"][
                            hunk_id
                        ]  # Replace with actual suggested improvements
                        break

                review["need_update"].append(update_data)

    # Generate overall comment
    commit_summary = "\n".join(
        [f"- {msg.split('\n')[0]}" for msg in pr_data["commit_messages"][:3]]
    )
    if len(pr_data["commit_messages"]) > 3:
        commit_summary += (
            f"\n- ... and {len(pr_data['commit_messages']) - 3} more commits"
        )

    review[
        "comment"
    ] = f"""PR Review: {pr_data['pr_title']}

The developer ({pr_data['pr_author']}) has made changes across {len(pr_data['file_changes'])} files.

Commit messages:
{commit_summary}

Description:
{pr_data['pr_description'] or 'No description provided'}

The changes appear to focus on {pr_data['pr_title'].lower()}.
"""

    return review


# Example usage
if __name__ == "__main__":
    # Replace these with your actual values
    ACCESS_TOKEN = "github_pat_11A3JWIVQ0zTy1uVNcLCYh_MWGDOGGf7Ta5GPxKHcfLH2FbxBN07T3XYcpLmuatgoWEQXU75OHYdiw1"
    REPO_OWNER = "code100x"
    REPO_NAME = "daily-code"
    PR_NUMBER = 742  # Specific PR number from your example

    # Extract PR changes
    pr_data = extract_pr_changes(ACCESS_TOKEN, REPO_OWNER, REPO_NAME, PR_NUMBER)

    # Generate review (this is where you would add your AI analysis)
    review = generate_pr_review(pr_data)

    # Output as JSON
    print(json.dumps(review, indent=2))

    # You could also write to a file
    with open(f"pr_{PR_NUMBER}_review.json", "w") as f:
        json.dumps(review, f, indent=2)
