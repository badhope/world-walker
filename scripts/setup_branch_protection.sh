#!/usr/bin/env bash
# Branch Protection Setup Script
# ===============================
# Configures GitHub branch protection rules for the `main` and `develop` branches
# to satisfy OpenSSF Scorecard "Branch-Protection" check.
#
# Prerequisites:
#   - gh CLI authenticated (gh auth login)
#   - admin access to the repository
#
# Usage:
#   ./scripts/setup_branch_protection.sh
#
# Reference:
#   https://docs.github.com/en/repositories/configuring-branches-and-merges-on-your-repository/managing-protected-branches/about-protected-branches
#   https://github.com/ossf/scorecard/blob/main/checks/branch_protection.md

set -euo pipefail

REPO="${GITHUB_REPOSITORY:-badhope/national_stats}"
BRANCHES=("main" "develop")

echo "[sec] Configuring branch protection for ${REPO}"
echo ""

# Check prerequisites
if ! command -v gh >/dev/null 2>&1; then
    echo "[x] GitHub CLI (gh) not found. Install: https://cli.github.com/"
    exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
    echo "[x] Not authenticated. Run: gh auth login"
    exit 1
fi

for BRANCH in "${BRANCHES[@]}"; do
    echo "--------------------"
    echo " Branch: ${BRANCH}"
    echo "--------------------"

    # Use gh api to PUT branch protection rules
    gh api \
        --method PUT \
        -H "Accept: application/vnd.github+json" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        "/repos/${REPO}/branches/${BRANCH}/protection" \
        --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "CI / test (3.11)",
      "CI / test (3.12)",
      "CI / lint",
      "Frontend Validation / validate",
      "CodeQL"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismissal_restrictions": {},
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1,
    "require_last_push_approval": true
  },
  "restrictions": {
    "users": [],
    "teams": ["maintainers"],
    "apps": []
  },
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": false
}
EOF

    # Enable auto-merge for dependabot PRs
    gh api \
        --method PATCH \
        -H "Accept: application/vnd.github+json" \
        "/repos/${REPO}" \
        --input - <<EOF
{
  "allow_auto_merge": true,
  "delete_branch_on_merge": true,
  "allow_squash_merge": true,
  "allow_merge_commit": false,
  "allow_rebase_merge": true,
  "squash_merge_commit_message": "BLANK",
  "squash_merge_commit_title": "PR_TITLE",
  "merge_commit_message": "PR_TITLE",
  "merge_commit_title": "MERGE_MESSAGE"
}
EOF

    echo "[ok] ${BRANCH} protection configured"
    echo ""
done

echo "--------------------"
echo " Branch protection setup complete!"
echo ""
echo "Configured for: ${BRANCHES[*]}"
echo "Repository:     ${REPO}"
echo ""
echo "Rules enabled:"
echo "  [ok] Required status checks (CI, Frontend, CodeQL)"
echo "  [ok] Required pull request reviews (1+ approver, code owner)"
echo "  [ok] Dismiss stale approvals on new push"
echo "  [ok] Require last push approval"
echo "  [ok] Require conversation resolution"
echo "  [ok] Linear history required"
echo "  [ok] Force push disabled"
echo "  [ok] Branch deletion disabled"
echo "  [ok] Admin enforcement enabled"
echo "  [ok] Auto-merge enabled"
echo "  [ok] Delete branch on merge enabled"
