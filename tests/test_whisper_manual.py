from openai import OpenAI

client = OpenAI()

with open("assets/test_audio.mp4", "rb") as f:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=f
    )

print(transcript.text)