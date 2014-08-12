## SublimeText Redmine Client

SublimeText Plugin to interact with Redmine right in your editor.

### Quick Start
- Clone/download plugin to your SublimeText User folder under SubRed

### Configure

##### Basic
Set the `redmine_url` and `api_key` in `Preferences: Package Settings > SublimeCombineMediaQueries > Settings – User`:

```
{
  "redmine_url" : "URL to your Redmine",
  "api_key": "Set your Redmine API Key"
}
```

##### Hotkeys
`Preferences: Package Settings > SublimeCombineMediaQueries > Settings – User`:
Hotkeys configuration:

```
  {
    "keys": ["shift+command+k"],
    "command": "sub_red"
  },
  {
    "keys": ["shift+command+h"],
    "command": "sub_red_refresh"
  }
```

### Functions

##### 1. View Redmine Issue right in you SublimeText view pane.
Hit `shift+command+k` and enter Issue ID:

![Search for issue](screenshots/search_id.png?raw=true)

New view will open for each issue you search:
![Issue served](screenshots/issue.png?raw=true)

`shift+command+h` to change issue status

![Issue served](screenshots/set_status.png?raw=true)

### Why?

I really hate to open browser, navigate to Redmine and look for issue when I need only to take a look on it.

