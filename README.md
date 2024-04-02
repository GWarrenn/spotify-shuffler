<h3 align="center">🔀 Spotify Shuffler 🔀</h3>

---

I think Spotify is great at many things -- maybe not so great at actually paying artists -- but great for me to listen to music and discover new artists. However, my biggest complaint is that there isn't really such a concept of "my library" of music. In the good old days of iTunes (or VLC) when you could just shuffle your library of music without having to think of a specific playlist. Maybe I'm just lazy but the act of creating dozens of playlists doesn't appeal to me and Spotify's "smart shuffle" feature will try and get me to listen to new music, which is great, but there are some days where I just want to listen to my library. I've also found that Spotify's UI is great at suggesting bands you're currently listening to over and over, which has led to some ... repetitive listening over the years.

So, in an effort to re-create the magic of shuffling through my library, I created this project. Thanks to Spotify (and [Article 15 of the GDPR forcing them to](https://support.spotify.com/us/article/gdpr-article-15-information/?ref=related)) allowing users to download all of their historical listening data through [this slightly buried link](https://www.spotify.com/us/account/privacy/). The download request takes a few weeks, so it's not super efficient. I host the data on my Google Drive which can be accessed by the main Python code running on a Render cron, which will randomly select songs -- ensuring that each artist is equally represented -- and post them to a new daily Spotify playlist that I can just shuffle throughout the day. 

So far, I've found that this has helped me rediscover some of the bangers that I loved many years ago but haven't thought to relisten to in recent years and has even helped me rediscover some of the songs that Spotify showed to me many years ago but hasn't since suggested.

![image](https://github.com/GWarrenn/spotify-shuffler/assets/6651576/f83cbb71-6a38-4bfd-b966-5bbf1200e4de)
