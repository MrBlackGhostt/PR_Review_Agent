import base64
from typing import Union
import requests
from fastapi import FastAPI
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

token = os.getenv("GITHUB_TOKEN")


# def pr():
#     headers = {"Authorization": f"Bearer {token}"}
#     res = requests.get(
#         "https://api.github.com/repos/code100x/daily-code/pulls/742/files"
#     )
#     print(res.json())
#     # message.append({"role": "user", "content": str(res.json())})
#     return


@app.get("/")
def start():
    return {"req": "start"}


@app.get("/pr")
def read_root():
    res = requests.get("https://api.github.com/repos/langfuse/langfuse/pulls/6647")
    print("RESPONSE", res.json())
    return res.json()

    # Make sure token is defined before using it
    token = "your_github_token"  # Replace with your actual token
    headers = {"Authorization": f"Bearer {token}"}

    # Get PR files
    files_response = requests.get(
        "https://api.github.com/repos/code100x/daily-code/pulls/742/files",
        headers=headers,
    )
    files_data = files_response.json()

    # Get PR details
    pr_response = requests.get(
        "https://api.github.com/repos/code100x/daily-code/pulls/742", headers=headers
    )
    pr_data = pr_response.json()

    # Get PR commits to extract commit messages
    commits_response = requests.get(
        "https://api.github.com/repos/code100x/daily-code/pulls/742/commits",
        headers=headers,
    )
    commits_data = commits_response.json()

    # Extract commit messages
    commit_messages = [commit["commit"]["message"] for commit in commits_data]

    # Process file changes
    file_changes = []

    for file in files_data:
        file_path = file["filename"]

        # For getting full file content before and after changes
        # (This is a more reliable approach than trying to reconstruct from the patch)
        if file["status"] != "added":
            # Get the file before the changes
            before_response = requests.get(
                f"https://api.github.com/repos/code100x/daily-code/contents/{file_path}?ref={pr_data['base']['sha']}",
                headers=headers,
            )
            if before_response.status_code == 200:
                before_data = before_response.json()
                before_content = base64.b64decode(before_data["content"]).decode(
                    "utf-8"
                )
            else:
                before_content = "Unable to retrieve original content"
        else:
            before_content = ""

        if file["status"] != "removed":
            # Get the file after the changes
            after_response = requests.get(
                f"https://api.github.com/repos/code100x/daily-code/contents/{file_path}?ref={pr_data['head']['sha']}",
                headers=headers,
            )
            if after_response.status_code == 200:
                after_data = after_response.json()
                after_content = base64.b64decode(after_data["content"]).decode("utf-8")
            else:
                after_content = "Unable to retrieve updated content"
        else:
            after_content = ""

        file_change = {
            "file_path": file_path,
            "status": file["status"],
            "additions": file["additions"],
            "deletions": file["deletions"],
            "before_content": before_content,
            "after_content": after_content,
            "patch": file.get("patch", ""),  # Include the patch for reference
        }

        file_changes.append(file_change)

    result = {
        "pr_title": pr_data.get("title", ""),
        "pr_description": pr_data.get("body", ""),
        "commit_messages": commit_messages,
        "file_changes": file_changes,
    }
    print("RESULT", result)

    return result


def pr():
    import requests
    import json

    # Get PR files without requiring a token
    files_response = requests.get(
        "https://api.github.com/repos/code100x/daily-code/pulls/742/files"
    )

    # Debug information
    print("Files response status:", files_response.status_code)

    try:
        # Try to parse the JSON response
        if isinstance(files_response.text, str):
            files_data = json.loads(files_response.text)
        else:
            files_data = files_response.json()

        # Debug the parsed data
        print("Files data type:", type(files_data))

        # Process file changes
        file_changes = []

        if isinstance(files_data, list):
            for file in files_data:
                if isinstance(file, dict) and "filename" in file:
                    file_path = file["filename"]

                    file_change = {
                        "file_path": file_path,
                        "status": file.get("status", ""),
                        "additions": file.get("additions", 0),
                        "deletions": file.get("deletions", 0),
                        "patch": file.get("patch", ""),
                    }

                    file_changes.append(file_change)
                else:
                    print(f"Unexpected file format: {file}")
        else:
            print(f"Unexpected files_data format: {files_data}")

        result = {"file_changes": file_changes}

        # Try to get the commit message from the PR title as a fallback
        try:
            pr_response = requests.get(
                "https://api.github.com/repos/code100x/daily-code/pulls/708"
            )
            if pr_response.status_code == 200:
                pr_data = (
                    json.loads(pr_response.text)
                    if isinstance(pr_response.text, str)
                    else pr_response.json()
                )
                if isinstance(pr_data, dict):
                    result["pr_title"] = pr_data.get("title", "")
                    result["pr_description"] = pr_data.get("body", "")
        except Exception as e:
            print(f"Error getting PR details: {e}")
        # print("Result", result)
        return result

    except Exception as e:
        print(f"Error processing PR data: {e}")
        return {"error": str(e)}
