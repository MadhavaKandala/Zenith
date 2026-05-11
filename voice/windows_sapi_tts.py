import asyncio
import base64
import subprocess
import tempfile
import uuid
import wave
from pathlib import Path

from livekit.agents import DEFAULT_API_CONNECT_OPTIONS, APIConnectOptions, tts


class WindowsSapiTTS(tts.TTS):
    def __init__(self, *, speaking_rate: int = 0) -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=16000,
            num_channels=1,
        )
        self._speaking_rate = speaking_rate
        self._work_dir = Path(tempfile.gettempdir()) / "zenith-sapi-tts"
        self._work_dir.mkdir(parents=True, exist_ok=True)

    @property
    def provider(self) -> str:
        return "windows"

    @property
    def model(self) -> str:
        return "sapi"

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> tts.ChunkedStream:
        return _WindowsSapiChunkedStream(
            tts=self,
            input_text=text,
            conn_options=conn_options,
        )

    async def aclose(self) -> None:
        return None

    async def synthesize_to_wave_file(self, text: str, output_path: Path) -> None:
        text_b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
        path_b64 = base64.b64encode(str(output_path).encode("utf-8")).decode("ascii")
        script = f"""
Add-Type -AssemblyName System.Speech
$text = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('{text_b64}'))
$path = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('{path_b64}'))
$format = [System.Speech.AudioFormat.SpeechAudioFormatInfo]::new(
    16000,
    [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,
    [System.Speech.AudioFormat.AudioChannel]::Mono
)
$synth = [System.Speech.Synthesis.SpeechSynthesizer]::new()
$synth.Rate = {self._speaking_rate}
$synth.SetOutputToWaveFile($path, $format)
$synth.Speak($text)
$synth.Dispose()
"""

        process = await asyncio.create_subprocess_exec(
            "pwsh",
            "-NoProfile",
            "-Command",
            script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        _stdout, stderr = await process.communicate()
        if process.returncode != 0:
            error_text = stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"Windows SAPI TTS failed: {error_text or process.returncode}")


class _WindowsSapiChunkedStream(tts.ChunkedStream):
    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        output_emitter.initialize(
            request_id=uuid.uuid4().hex,
            sample_rate=self._tts.sample_rate,
            num_channels=self._tts.num_channels,
            mime_type="audio/pcm",
            stream=False,
        )

        wav_path = self._tts._work_dir / f"{uuid.uuid4().hex}.wav"
        try:
            await self._tts.synthesize_to_wave_file(self._input_text, wav_path)

            with wave.open(str(wav_path), "rb") as wav_file:
                if wav_file.getframerate() != self._tts.sample_rate:
                    raise RuntimeError(
                        f"Unexpected sample rate: {wav_file.getframerate()}"
                    )
                if wav_file.getnchannels() != self._tts.num_channels:
                    raise RuntimeError(
                        f"Unexpected channel count: {wav_file.getnchannels()}"
                    )
                if wav_file.getsampwidth() != 2:
                    raise RuntimeError(
                        f"Unexpected sample width: {wav_file.getsampwidth()}"
                    )

                chunk_frames = self._tts.sample_rate // 10
                while True:
                    pcm_bytes = wav_file.readframes(chunk_frames)
                    if not pcm_bytes:
                        break
                    output_emitter.push(pcm_bytes)

            output_emitter.flush()
        finally:
            wav_path.unlink(missing_ok=True)
