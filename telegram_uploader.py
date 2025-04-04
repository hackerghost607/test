import sqlite3
import json
import os
import requests
import tempfile
from pathlib import Path
import time
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.tl.types import DocumentAttributeVideo
import asyncio

# Telegram configuration
API_ID = "20765358"
API_HASH = "5265d01feb3d4aeaea14af77ab527a65"
PHONE_NUMBER = "+251715560694"
CHANNEL_ID = "https://t.me/+sOiKtIvNNsA4MzE8"

# Database configuration
DB_PATH = "downloads.db"
OUTPUT_JSON = "telegram_file_ids.json"
SESSION_FILE = "anime_sender_session"

# Rate limiting configuration
RATE_LIMIT_DELAY = 30  # seconds between uploads
MAX_RETRIES = 3
RETRY_DELAY = 60  # seconds to wait after hitting rate limit

class RateLimiter:
    def __init__(self, delay_seconds):
        self.delay_seconds = delay_seconds
        self.last_request_time = datetime.min

    def wait(self):
        now = datetime.now()
        time_since_last = (now - self.last_request_time).total_seconds()
        if time_since_last < self.delay_seconds:
            sleep_time = self.delay_seconds - time_since_last
            print(f"Rate limiting: Waiting {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
        self.last_request_time = datetime.now()

rate_limiter = RateLimiter(RATE_LIMIT_DELAY)

# Initialize Telegram client with session
client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

async def ensure_authorized():
    """Ensure the client is authorized and session is saved"""
    if not await client.is_user_authorized():
        print("Session not found or expired. Starting authorization...")
        await client.start(phone=PHONE_NUMBER)
        print("Authorization successful! Session has been saved.")
    else:
        print("Using existing session.")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def load_existing_file_ids():
    if os.path.exists(OUTPUT_JSON):
        with open(OUTPUT_JSON, 'r') as f:
            return json.load(f)
    return {}

def save_file_ids(file_ids):
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(file_ids, f, indent=4)

def download_video(url):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    
    # Download the file in chunks
    with open(temp_file.name, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    
    return temp_file.name

async def upload_to_telegram(file_path, anime_id, episode_number):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            # Wait for rate limit
            rate_limiter.wait()
            
            # Upload the video to Telegram
            message = await client.send_file(
                CHANNEL_ID,
                file_path,
                caption=f"Anime ID: {anime_id}\nEpisode: {episode_number}",
                attributes=[DocumentAttributeVideo(
                    duration=0,  # Duration will be set automatically
                    w=0,  # Width will be set automatically
                    h=0,  # Height will be set automatically
                    supports_streaming=True
                )]
            )
            
            # Get the file_id from the sent message
            file_id = message.media.document.id
            
            # Clean up the temporary file
            os.unlink(file_path)
            
            return str(file_id)
            
        except Exception as e:
            error_msg = str(e).lower()
            retries += 1
            
            # Check if it's a rate limit error
            if "too many requests" in error_msg or "flood" in error_msg:
                print(f"Rate limit hit. Waiting {RETRY_DELAY} seconds before retry {retries}/{MAX_RETRIES}")
                time.sleep(RETRY_DELAY)
                continue
            else:
                print(f"Error uploading to Telegram: {e}")
                if os.path.exists(file_path):
                    os.unlink(file_path)
                return None
    
    print(f"Failed to upload after {MAX_RETRIES} retries")
    if os.path.exists(file_path):
        os.unlink(file_path)
    return None

async def process_episodes():
    # Load existing file IDs
    file_ids = load_existing_file_ids()
    
    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get all episodes that haven't been processed yet
        cursor.execute("""
            SELECT e.anime_id, e.episode_number, e.download_url 
            FROM episodes e
            WHERE NOT EXISTS (
                SELECT 1 FROM json_each(?) 
                WHERE json_extract(value, '$.anime_id') = e.anime_id 
                AND json_extract(value, '$.episode_number') = e.episode_number
            )
        """, (json.dumps(list(file_ids.values())),))
        
        episodes = cursor.fetchall()
        total_episodes = len(episodes)
        
        print(f"Found {total_episodes} episodes to process")
        
        for index, (anime_id, episode_number, download_url) in enumerate(episodes, 1):
            print(f"Processing {index}/{total_episodes}: anime_id: {anime_id}, episode: {episode_number}")
            
            try:
                # Download the video
                print(f"Downloading video...")
                temp_file_path = download_video(download_url)
                
                # Upload to Telegram
                print(f"Uploading to Telegram...")
                file_id = await upload_to_telegram(temp_file_path, anime_id, episode_number)
                
                if file_id:
                    # Save the file ID
                    file_ids[f"{anime_id}_{episode_number}"] = {
                        "anime_id": anime_id,
                        "episode_number": episode_number,
                        "file_id": file_id
                    }
                    
                    # Save after each successful upload
                    save_file_ids(file_ids)
                    print(f"Successfully processed anime_id: {anime_id}, episode: {episode_number}")
                else:
                    print(f"Failed to upload anime_id: {anime_id}, episode: {episode_number}")
            
            except Exception as e:
                print(f"Error processing anime_id: {anime_id}, episode: {episode_number}: {e}")
                continue
    
    finally:
        conn.close()

async def main():
    try:
        # Ensure we're authorized and session is saved
        await ensure_authorized()
        
        # Process episodes
        await process_episodes()
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Properly disconnect the client
        await client.disconnect()

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main()) 