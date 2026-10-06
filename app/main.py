from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from urllib.parse import urlparse, parse_qs
import re

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    VideoUnavailable,
    RequestBlocked,
    IpBlocked,
)

app = FastAPI(
    title="YouTube Transcript Server",
    version="1.0.0",
    description="A small API wrapper around youtube-transcript-api.",
)

ytt_api = YouTubeTranscriptApi()


class TranscriptRequest(BaseModel):
    url: str = Field(..., description="A YouTube video URL")
    languages: list[str] = Field(default=["en"], description="Language codes in priority order")
    preserve_formatting: bool = False


def extract_video_id(url: str) -> str:
    """Extract a YouTube video ID from common YouTube URL formats."""
    parsed = urlparse(url)

    if parsed.hostname in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.lstrip("/").split("/")[0]
    elif parsed.hostname in {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "music.youtube.com",
    }:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]
        elif parsed.path.startswith("/shorts/"):
            video_id = parsed.path.split("/shorts/")[1].split("/")[0]
        elif parsed.path.startswith("/embed/"):
            video_id = parsed.path.split("/embed/")[1].split("/")[0]
        else:
            video_id = None
    else:
        video_id = None

    if not video_id or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    return video_id


@app.get("/")
def root():
    return {
        "name": "YouTube Transcript Server",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/transcript")
def get_transcript(request: TranscriptRequest):
    video_id = extract_video_id(request.url)

    try:
        transcript = ytt_api.fetch(
            video_id,
            languages=request.languages,
            preserve_formatting=request.preserve_formatting,
        )

        snippets = transcript.to_raw_data()

        return {
            "success": True,
            "video_id": transcript.video_id,
            "language": transcript.language,
            "language_code": transcript.language_code,
            "is_generated": transcript.is_generated,
            "transcript": snippets,
            "text": " ".join(item["text"] for item in snippets),
        }

    except VideoUnavailable:
        raise HTTPException(status_code=404, detail="YouTube video is unavailable")
    except NoTranscriptFound:
        raise HTTPException(
            status_code=404,
            detail=f"No transcript found for languages: {request.languages}",
        )
    except (RequestBlocked, IpBlocked):
        raise HTTPException(
            status_code=503,
            detail="YouTube blocked the server IP. A rotating residential proxy may be required.",
        )
    except CouldNotRetrieveTranscript:
        raise HTTPException(
            status_code=502,
            detail="YouTube transcript could not be retrieved.",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")


@app.get("/transcripts/{video_id}")
def list_transcripts(video_id: str):
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise HTTPException(status_code=400, detail="Invalid YouTube video ID")

    try:
        transcript_list = ytt_api.list(video_id)

        return {
            "success": True,
            "video_id": video_id,
            "transcripts": [
                {
                    "language": transcript.language,
                    "language_code": transcript.language_code,
                    "is_generated": transcript.is_generated,
                    "is_translatable": transcript.is_translatable,
                    "translation_languages": transcript.translation_languages,
                }
                for transcript in transcript_list
            ],
        }
    except VideoUnavailable:
        raise HTTPException(status_code=404, detail="YouTube video is unavailable")
    except (RequestBlocked, IpBlocked):
        raise HTTPException(
            status_code=503,
            detail="YouTube blocked the server IP. A rotating residential proxy may be required.",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")
