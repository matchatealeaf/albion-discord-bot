# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 2020-04-30

### Changes

- Changed checking of member roles before and after a role change in the unused cog `talk.py`, for convenience in specifying which roles to send a PM to.

## 2020-03-01

### Added

- Added buy order prices.

## 2020-02-20

### Fixes

- Fixed embed not showing up.
	- Now no longer show 0 entries.

## 2020-02-10

### Added

- Added gold prices plotting command.
	- `emilie gold <number of days to plot>`.
	- For example, `emilie gold 7` will plot gold prices for the past 7 days.
	- Also list past 6 hours gold prices.

### Fixes

- Rolled back to old JSON entries' names with snake_case.
	- Fixed "NO DATA" error.

## 2020-02-08

### Added

- Item search now support different localizations. (Not perfect, further improvements coming soon.)
	- Try `emilie price 土豆`, `emilie price картофель`, etc.

### Changes

- Removed 7 days plot for Outlands' markets: Arthur's Rest, Merlyn's Rest, Morgana's Rest.
	- Since data for them are scarce, the plots just takes up space.

### Fixes

- Fixed redundancy when getting historical data.
	- Huge increased in query speed.

### Removed

- Removed Jaccard edit distance function for item matching, difflib will suffice.

## 2020-02-06

### Added

- Added Black Market.

## 2020-02-02

### Added

- Added Outlands' markets: Arthur's Rest, Merlyn's Rest, Morgana's Rest.
	- Historical plot is plotted separately due to the huge price difference from Royal markets.
- Added new command prefixes `e! ` and `@mention bot ` for people who can't spell Emilie.
	- Examples: `e! price t5 hide`, `@Assistant Emilie price t6 rock`.

### Changes

- Moved historical plot's legends outside of the plot for clarity.

### Bug Fixes

- Fixed a bug that prevent using the `quick` command if command prefix has no spaces.
- Debug message of `eval` command is now labeled as 'eval' rather than 'exec'.

## 2020-02-01

### Changes

- Changed file lookup to real path instead of relative to working directory.
	- This fixed issues when working directory is not in the same folder as **main.py**.

## 2020-01-30

### Changes

- Code formatting is now done with [Black](https://github.com/psf/black)

## 2020-01-28

### Changes

- User-defined configs are now moved to [config.ini] file.
- Updated README.md with new instructions for [config.ini] file.

### Added

- Logging. The bot now logs debug messages to a discord.log file.
- Added [.gitignore]
 	- *.pyc
	- plot.png
	- *.log

## 2020-01-25

- Initial Commit

[config.ini]: https://github.com/matchatealeaf/albion-discord-bot/blob/master/config.ini
[.gitignore]: https://github.com/matchatealeaf/albion-discord-bot/blob/master/.gitignore

