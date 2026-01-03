# commit

Execute `git diff origin/master`, messages from `git log ..origin/master` and content of affected files to take context of current changes.
According to uncommitted changes prepare "COMMIT MESSAGE".
If "COMMIT MESSAGE" already present - adjust it.
In ideal way commit title should looks like "{ISSUE-NUM}: MODULE_NAME: changes description"
Prefer short text to fill "COMMIT MESSAGE"
If code with breaking changes present - mark it! But not mark if "No breaking changes".
Do not execute `git commit`!
