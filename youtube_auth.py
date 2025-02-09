import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import re
from rapidfuzz import fuzz

# Spotify API Credentials
SPOTIFY_CLIENT_ID = "abcc07b3403f45248aa8a4f7d5ce4209"
SPOTIFY_CLIENT_SECRET = "0f571951d1e64e3180a6203853a81a32"
SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"

# YouTube Playlist URL
#YOUTUBE_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLh-IkQZn6oYz1DMl8H8uKai4Hv9zqrv-5"

# Authenticate with Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="playlist-modify-public"
))

def get_youtube_playlist_titles(url):
    """Extracts video titles from a YouTube playlist using yt-dlp."""
    ydl_opts = {'quiet': False, 'extract_flat': True, 'playlistend': 50}
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        if 'entries' not in info or not info['entries']:
            print("❌ Error: No 'entries' found. Ensure the playlist is public.")
            return []
        
        titles = [entry.get('title', 'Unknown Title') for entry in info['entries']]
        print("🎵 Extracted YouTube Titles:", titles)
        return titles

def clean_title(title):
    """Cleans YouTube song titles but keeps artist names intact."""
    title = re.sub(r"\(.*?\)|\[.*?\]", "", title)  # Remove text in brackets
    title = re.sub(r"\s*[-|]\s*", " - ", title)  # Standardize separators
    common_words = ["official music video", "official video", "lyrics", "audio", "HD", "4K", "remix", "live", "feat."]
    
    for word in common_words:
        title = re.sub(rf"\b{word}\b", "", title, flags=re.IGNORECASE)

    title = re.sub(r"\s+", " ", title).strip()  # Normalize spaces
    return title

def extract_artist_and_title(title):
    """Extracts artist and song name from a YouTube title."""
    parts = title.split(" - ", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return None, title  # No artist found, treat whole title as song name

def search_spotify_track(title):
    """Searches for a song on Spotify and selects the best match."""
    cleaned_title = clean_title(title)
    artist, song_name = extract_artist_and_title(cleaned_title)
    
    search_queries = [
        f"{song_name} {artist}" if artist else song_name,
        song_name,
        f"{song_name} track",
        f"{song_name} song"
    ]

    best_match = None
    highest_score = 0
    track_ids = set()  # To prevent duplicates

    print(f"🔍 Searching Spotify for: {title} (Cleaned: {cleaned_title})")

    for query in search_queries:
        result = sp.search(q=query, type='track', limit=5)

        for track in result['tracks']['items']:
            spotify_title = track['name']
            spotify_artist = track['artists'][0]['name']
            combined_spotify_title = f"{spotify_title} {spotify_artist}"
            
            # Fuzzy matching: Title and Artist
            title_score = fuzz.ratio(song_name.lower(), spotify_title.lower())
            artist_score = fuzz.ratio(artist.lower(), spotify_artist.lower()) if artist else 0
            match_score = (title_score * 0.7) + (artist_score * 0.3)

            print(f"🔹 Checking: {spotify_title} by {spotify_artist} | Score: {match_score}")

            if match_score > highest_score:
                highest_score = match_score
                best_match = track['id']
                track_ids.add(track['id'])  # Prevent duplicates

    if highest_score >= 50:  # Lowered threshold for better matches
        print(f"✅ Best Match: {spotify_title} by {spotify_artist} (Score: {highest_score})")
        return best_match

    print(f"❌ No good match for: {title} (Cleaned: {cleaned_title})")
    return None

def create_spotify_playlist(name="YouTube Playlist"):
    """Creates a new Spotify playlist and returns its ID."""
    user_id = sp.me()['id']
    playlist = sp.user_playlist_create(user_id, name, public=True)
    print(f"✅ Created Spotify Playlist: {name} | ID: {playlist['id']}")
    return playlist['id']

def add_songs_to_spotify_playlist(playlist_id, song_titles):
    """Searches for songs on Spotify and adds them to the playlist."""
    track_ids = set()  # Prevent duplicates

    for title in song_titles:
        track_id = search_spotify_track(title)
        if track_id and track_id not in track_ids:
            track_ids.add(track_id)
        else:
            print(f"🚨 No match found for: {title}")

    print(f"🎵 Total songs matched: {len(track_ids)}")

    if not track_ids:
        print("❌ No valid Spotify tracks found. Skipping playlist update.")
        return

    try:
        for i in range(0, len(track_ids), 100):  # Batch adding due to API limit
            batch = list(track_ids)[i:i+100]
            response = sp.playlist_add_items(playlist_id, batch)
            print(f"✅ Added {len(batch)} songs to Spotify playlist. Response: {response}")
    except Exception as e:
        print(f"❌ Error adding songs to Spotify playlist: {str(e)}")

# Run the script
#youtube_titles = get_youtube_playlist_titles(YOUTUBE_PLAYLIST_URL)

#if youtube_titles:
    #spotify_playlist_id = create_spotify_playlist()
    #add_songs_to_spotify_playlist(spotify_playlist_id, youtube_titles)
    #print("✅ Playlist created and songs added successfully!")
#else:
    #print("❌ No YouTube titles extracted. Stopping script.")
# Ask the user for the YouTube playlist URL
youtube_url = input("🎵 Enter the YouTube playlist URL: ")

# Run the script
if youtube_url.strip():
    youtube_titles = get_youtube_playlist_titles(youtube_url)

    if youtube_titles:
        spotify_playlist_id = create_spotify_playlist()
        add_songs_to_spotify_playlist(spotify_playlist_id, youtube_titles)
        print("✅ Playlist created and songs added successfully!")
    else:
        print("❌ No YouTube titles extracted. Stopping script.")
else:
    print("❌ No URL provided. Exiting script.")
