<p align="center">
  <img src="https://files.catbox.moe/kjr0cd.png" width="720" alt="infrared banner"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/module-infrared.fm-7a0f17?style=flat&labelColor=000000" />
  <img src="https://img.shields.io/badge/api-last.fm-7a0f17?style=flat&labelColor=000000" />
  <img src="https://img.shields.io/badge/status-private-7a0f17?style=flat&labelColor=000000" />
</p>

<br>

<blockquote align="center">
  <em>maybe we scrobble.<br>maybe we don’t.</em>
</blockquote>

---

### what is this

infrared.fm  
a lowkey async wrapper for last.fm  
built for the bot. kept for the flex.

- users, tracks, artists, albums, charts  
- fast. minimal. wrapped in black.

---

### how to

```py
from infrared.fm import LastFM

lfm = LastFM(api_key="...")
user = await lfm.get_user("...")
np = await lfm.now_playing(user.name)
