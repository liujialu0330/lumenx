"""
Text-to-Speech (TTS) module supporting multiple providers.

Providers:
  - cosyvoice (default): DashScope CosyVoice API
  - doubao: Volcengine TTS HTTP API (openspeech.bytedance.com)

Factory function create_tts_processor() selects implementation based on TTS_PROVIDER env var.
"""
import os
import logging
import uuid
import base64
import time
import requests
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


# Voice registry: key -> {model_id, name, gender, model}
# model_id must match the model version (v2 voices for cosyvoice-v2, v3 for cosyvoice-v3-*)
# Reference: https://help.aliyun.com/zh/model-studio/cosyvoice-voice-list
VOICES = {
    # === cosyvoice-v2 voices ===
    'longxiaochun': {'model_id': 'longxiaochun_v2', 'name': '龙小淳 (知性女)', 'gender': 'Female', 'model': 'cosyvoice-v2'},
    'longxiaoxia': {'model_id': 'longxiaoxia_v2', 'name': '龙小夏 (沉稳女)', 'gender': 'Female', 'model': 'cosyvoice-v2'},
    'longyue': {'model_id': 'longyue_v2', 'name': '龙悦 (温柔女)', 'gender': 'Female', 'model': 'cosyvoice-v2'},
    'longmiao': {'model_id': 'longmiao_v2', 'name': '龙淼 (有声书女)', 'gender': 'Female', 'model': 'cosyvoice-v2'},
    'longyuan': {'model_id': 'longyuan_v2', 'name': '龙媛 (治愈女)', 'gender': 'Female', 'model': 'cosyvoice-v2'},
    'longhua': {'model_id': 'longhua_v2', 'name': '龙华 (活力甜美女)', 'gender': 'Female', 'model': 'cosyvoice-v2'},
    'longwan': {'model_id': 'longwan_v2', 'name': '龙婉 (知性女)', 'gender': 'Female', 'model': 'cosyvoice-v2'},
    'longxing': {'model_id': 'longxing_v2', 'name': '龙星 (邻家女孩)', 'gender': 'Female', 'model': 'cosyvoice-v2'},
    'longfeifei': {'model_id': 'longfeifei_v2', 'name': '龙菲菲 (甜美女)', 'gender': 'Female', 'model': 'cosyvoice-v2'},
    'longyan': {'model_id': 'longyan_v2', 'name': '龙言 (温柔女)', 'gender': 'Female', 'model': 'cosyvoice-v2'},
    'longqiang': {'model_id': 'longqiang_v2', 'name': '龙蔷 (浪漫女)', 'gender': 'Female', 'model': 'cosyvoice-v2'},
    'longxiu': {'model_id': 'longxiu_v2', 'name': '龙修 (博学男)', 'gender': 'Male', 'model': 'cosyvoice-v2'},
    'longnan': {'model_id': 'longnan_v2', 'name': '龙楠 (睿智少年)', 'gender': 'Male', 'model': 'cosyvoice-v2'},
    'longcheng': {'model_id': 'longcheng_v2', 'name': '龙诚 (睿智青年)', 'gender': 'Male', 'model': 'cosyvoice-v2'},
    'longze': {'model_id': 'longze_v2', 'name': '龙泽 (阳光男)', 'gender': 'Male', 'model': 'cosyvoice-v2'},
    'longzhe': {'model_id': 'longzhe_v2', 'name': '龙哲 (暖心男)', 'gender': 'Male', 'model': 'cosyvoice-v2'},
    'longtian': {'model_id': 'longtian_v2', 'name': '龙天 (磁性男)', 'gender': 'Male', 'model': 'cosyvoice-v2'},
    'longhan': {'model_id': 'longhan_v2', 'name': '龙翰 (深情男)', 'gender': 'Male', 'model': 'cosyvoice-v2'},
    'longhao': {'model_id': 'longhao_v2', 'name': '龙浩 (忧郁男)', 'gender': 'Male', 'model': 'cosyvoice-v2'},
    'longshu': {'model_id': 'longshu_v2', 'name': '龙书 (播报男)', 'gender': 'Male', 'model': 'cosyvoice-v2'},
    'longshuo': {'model_id': 'longshuo_v2', 'name': '龙朔 (博学男)', 'gender': 'Male', 'model': 'cosyvoice-v2'},
    'longfei': {'model_id': 'longfei_v2', 'name': '龙飞 (磁性朗诵男)', 'gender': 'Male', 'model': 'cosyvoice-v2'},
    'longxiaocheng': {'model_id': 'longxiaocheng_v2', 'name': '龙小诚 (低音男)', 'gender': 'Male', 'model': 'cosyvoice-v2'},
    'longshao': {'model_id': 'longshao_v2', 'name': '龙少 (阳光男)', 'gender': 'Male', 'model': 'cosyvoice-v2'},
    'longjielidou': {'model_id': 'longjielidou_v2', 'name': '龙杰力豆 (童声男)', 'gender': 'Male', 'model': 'cosyvoice-v2'},
    'longhuhu': {'model_id': 'longhuhu', 'name': '龙虎虎 (童声女)', 'gender': 'Female', 'model': 'cosyvoice-v2'},
    'loongstella': {'model_id': 'loongstella_v2', 'name': 'Stella (English Female)', 'gender': 'Female', 'model': 'cosyvoice-v2'},
    'loongbella': {'model_id': 'loongbella_v2', 'name': 'Bella (English Female)', 'gender': 'Female', 'model': 'cosyvoice-v2'},
    # === cosyvoice-v3 voices (require cosyvoice-v3-flash or cosyvoice-v3-plus) ===
    'longanyang': {'model_id': 'longanyang', 'name': '龙安阳 (阳光少年)', 'gender': 'Male', 'model': 'cosyvoice-v3-flash'},
    'longanhuan': {'model_id': 'longanhuan', 'name': '龙安欢 (活力女)', 'gender': 'Female', 'model': 'cosyvoice-v3-flash'},
}


class TTSProcessor:
    """Text-to-Speech processor using CosyVoice"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "cosyvoice-v2",
        voice: str = "longxiaochun_v2"
    ):
        """
        Initialize TTS processor

        Args:
            api_key: DashScope API key. If None, will read from DASHSCOPE_API_KEY env var
            model: TTS model name (default: cosyvoice-v2)
            voice: Default voice ID (default: longxiaochun_v2)
        """
        import dashscope

        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        if self.api_key:
            dashscope.api_key = self.api_key

        self.model = model
        self.voice = voice

        logger.info(f"TTS Processor initialized with model={model}, voice={voice}")

    def synthesize(
        self,
        text: str,
        output_path: str,
        voice: Optional[str] = None,
        speech_rate: float = 1.0,
        pitch_rate: float = 1.0,
        volume: int = 50,
    ) -> Tuple[str, float, str]:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize (max 20,000 characters)
            output_path: Path to save audio file
            voice: Voice ID override (must match model version)
            speech_rate: Speech speed multiplier (0.5-2.0, default 1.0)
            pitch_rate: Pitch multiplier (0.5-2.0, default 1.0)
            volume: Volume level (0-100, default 50)

        Returns:
            Tuple[str, float, str]: (output_path, first_package_delay_ms, request_id)
        """
        from dashscope.audio.tts_v2 import SpeechSynthesizer

        start_time = time.time()
        voice = voice or self.voice

        # Resolve the correct model for the voice if it's a known voice
        model = self._resolve_model_for_voice(voice)

        logger.info(f"Synthesizing with model={model}, voice='{voice}' (rate={speech_rate}, pitch={pitch_rate}, vol={volume})...")
        logger.info(f"Text: {text[:100]}{'...' if len(text) > 100 else ''}")

        # Clamp parameters to valid ranges per DashScope docs
        speech_rate = max(0.5, min(2.0, speech_rate))
        pitch_rate = max(0.5, min(2.0, pitch_rate))
        volume = max(0, min(100, volume))

        synthesizer = SpeechSynthesizer(
            model=model,
            voice=voice,
            speech_rate=speech_rate,
            pitch_rate=pitch_rate,
            volume=volume,
        )

        # Synthesize audio (blocking call, returns bytes)
        audio_data = synthesizer.call(text)

        # Get metrics
        request_id = synthesizer.get_last_request_id()
        first_package_delay = synthesizer.get_first_package_delay()

        # Ensure output directory exists and save
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(audio_data)

        duration = time.time() - start_time
        logger.info(f"Audio synthesized: request_id={request_id}, delay={first_package_delay}ms, total={duration:.2f}s -> {output_path}")

        return output_path, first_package_delay, request_id

    def _resolve_model_for_voice(self, voice_id: str) -> str:
        """Resolve the correct model for a given voice ID.

        v2 voices require cosyvoice-v2, v3 voices require cosyvoice-v3-flash/plus.
        Falls back to self.model if voice is not in the registry (e.g. cloned voices).
        """
        for meta in VOICES.values():
            if meta['model_id'] == voice_id:
                return meta.get('model', self.model)
        return self.model

    @staticmethod
    def list_voices():
        """List available voices with metadata"""
        return VOICES


class DoubaoTTSProcessor:
    """Text-to-Speech processor using Volcengine TTS HTTP API (openspeech.bytedance.com)."""

    API_URL = "https://openspeech.bytedance.com/api/v1/tts"

    def __init__(
        self,
        appid: Optional[str] = None,
        token: Optional[str] = None,
        voice: str = "zh_female_wanwanxiaohe_moon_bigtts",
    ):
        self.appid = appid or os.getenv("VOLC_TTS_APPID")
        self.token = token or os.getenv("VOLC_TTS_TOKEN")
        self.voice = voice

        if not self.appid or not self.token:
            logger.warning("Volcengine TTS credentials not configured (VOLC_TTS_APPID / VOLC_TTS_TOKEN)")

        logger.info(f"DoubaoTTSProcessor initialized with voice={voice}")

    def synthesize(
        self,
        text: str,
        output_path: str,
        voice: Optional[str] = None,
        speech_rate: float = 1.0,
        pitch_rate: float = 1.0,
        volume: int = 50,
    ) -> Tuple[str, float, str]:
        """
        Synthesize speech via Volcengine TTS HTTP V1 API.

        Returns:
            Tuple[str, float, str]: (output_path, duration_ms, request_id)
        """
        start_time = time.time()
        voice = voice or self.voice
        reqid = str(uuid.uuid4())

        speed_ratio = max(0.1, min(2.0, speech_rate))
        loudness_ratio = max(0.5, min(2.0, volume / 50.0))

        payload = {
            "app": {
                "appid": self.appid,
                "token": self.token,
                "cluster": "volcano_tts",
            },
            "user": {
                "uid": "lumenx_user",
            },
            "audio": {
                "voice_type": voice,
                "encoding": "mp3",
                "speed_ratio": speed_ratio,
                "loudness_ratio": loudness_ratio,
            },
            "request": {
                "reqid": reqid,
                "text": text,
                "operation": "query",
            },
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer;{self.token}",
        }

        logger.info(f"Volcengine TTS: voice={voice}, text={text[:80]}...")

        try:
            resp = requests.post(self.API_URL, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            result = resp.json()

            code = result.get("code", -1)
            if code != 3000:
                raise RuntimeError(f"Volcengine TTS error code={code}: {result.get('message', '')}")

            audio_b64 = result.get("data", "")
            if not audio_b64:
                raise RuntimeError("Volcengine TTS returned empty audio data")

            audio_bytes = base64.b64decode(audio_b64)

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(audio_bytes)

            duration_ms = float(result.get("addition", {}).get("duration", "0"))
            total = time.time() - start_time
            logger.info(f"Volcengine TTS done: reqid={reqid}, audio_duration={duration_ms}ms, total={total:.2f}s -> {output_path}")

            return output_path, duration_ms, reqid

        except requests.RequestException as e:
            raise RuntimeError(f"Volcengine TTS request failed: {e}") from e

    @staticmethod
    def list_voices():
        """List available voices (placeholder - Volcengine has a separate voice list API)."""
        return {}


def create_tts_processor(provider: Optional[str] = None, **kwargs):
    """Factory: create TTS processor based on TTS_PROVIDER env var.

    Args:
        provider: Override provider selection ('cosyvoice' or 'doubao').
        **kwargs: Passed to the processor constructor.

    Returns:
        TTSProcessor or DoubaoTTSProcessor instance.
    """
    provider = provider or os.getenv("TTS_PROVIDER", "cosyvoice").lower()
    if provider == "doubao":
        return DoubaoTTSProcessor(**kwargs)
    return TTSProcessor(**kwargs)
