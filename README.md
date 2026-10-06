# YouTube Transcript Server

A small FastAPI service wrapping `youtube-transcript-api`.

## Local setup

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/health

## API

### POST /transcript

```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "languages": ["en"],
  "preserve_formatting": false
}
```

### GET /transcripts/{video_id}

Returns the transcript tracks available for a video.

## Render

Build command:

```text
pip install -r requirements.txt
```

Start command:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

The included `render.yaml` configures these automatically.

## Important

YouTube may block cloud-provider IPs. If the deployed service starts returning `RequestBlocked` or `IpBlocked`, add a rotating residential proxy and configure `YouTubeTranscriptApi` with the proxy settings supported by the library.
