#!/bin/bash

# Set GitHub credentials and repository info
GITHUB_USERNAME="sonotwildturtle"
GITHUB_TOKEN="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"
REPO_NAME="AlienDrop"
PRIVATE_REPO="true"

# Create a new GitHub repository using GitHub API
curl -u "$GITHUB_USERNAME:$GITHUB_TOKEN" https://api.github.com/user/repos -d '{
  "name": "'"$REPO_NAME"'",
  "private": '"$PRIVATE_REPO"'
}'

# Initialize Git repository
git init

# Add remote URL (this assumes your GitHub username and repository are correct)
git remote add origin https://"$GITHUB_USERNAME":"$GITHUB_TOKEN"@github.com/"$GITHUB_USERNAME"/"$REPO_NAME".git

# Add all files to the git repository
git add .

# Commit the changes
git commit -m "Initial commit"

# Push to the remote GitHub repository
git push -u origin master

