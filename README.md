# Keep Only Tags

## Overview

This plugin allows the user to determine which tags are written to the output files by Picard. Tags that you wish to keep are entered in a page in the options settings, with each tag on a separate line. Blank lines will be ignored. The entries are not case-sensitive.

If a tag in the list ends with an asterisk (\*), then it will keep any tags beginning with the tag. For example, if your list contains "**performer:\***" then all tags beginning with "**performer:**" will be kept, such as "**performer:instrument**" and "**performer:vocals**".

All tags that are removed will still be available as variables with "**\_ko\_**" prepended to the tag name. For example, if you choose not to keep the "**musicbrainz_trackid**" tag, it will still be available to scripts as "**_ko_musicbrainz_trackid**".

---

## What it Does

This plugin reads the album and track metadata provided to Picard and converts any tags not found in the user's "keep" list into hidden variables by adding "\_ko\_" to the start of the tag name.

***NOTE:*** This plugin is configured to run after all other plugins, so that it is working with the final information that may have been updated by another plugin.

---

## Caution

Any tags not included in the user's "keep" list are not available for use in scripts, including the file naming script. To accommodate the use of standard tags in the file naming script that have not been included in the "keep" list, you can include lines such as `$set(album,$if2(%album%,%_ko_album%))` at the beginning of file naming script for each of the tags used.
