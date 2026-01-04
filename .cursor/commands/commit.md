# commit

Execute `git diff origin/master`, messages from `git log ..origin/master` and content of affected files to take context of current changes.

According to uncommitted changes prepare ".git/COMMITMESSAGE".

If ".git/COMMITMESSAGE" already present - adjust it.

In ideal way commit title should looks like "{ISSUE-NUM}: MODULE_NAME: changes description".

Prefer short text to fill "COMMIT MESSAGE".

If code with breaking changes present - mark it with "BREAKING CHANGE:" in footer as described in Conventional Commits specification. 
But not mark if "No breaking changes".

Do not execute `git commit`!
