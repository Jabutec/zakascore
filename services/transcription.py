import io
import requests
from openai import OpenAI

client = OpenAI()


def transcribe_audio(audio_url: str, auth: tuple[str, str]) -> str | None:
    response = requests.get(audio_url, auth=auth)

    if response.status_code != 200:
        return None

    audio_file = io.BytesIO(response.content)
    audio_file.name = "audio.ogg"

    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )

    return transcript.text