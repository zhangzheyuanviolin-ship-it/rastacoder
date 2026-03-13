"""
Audio Tools - Audio processing, transcription, and manipulation

Specialized tools for audio-only operations that don't require video.
"""

import os
import json
from typing import Dict, List, Optional

from ..bridge import ToolError, get_bridge


def extract_audio(
    input_path: str,
    output_path: str,
    format: str = "mp3",
    bitrate: str = "192k"
) -> Dict:
    """
    Extract audio from video file.
    
    Args:
        input_path: Input video file path
        output_path: Output audio file path
        format: Output format (mp3, m4a, wav, flac, opus)
        bitrate: Audio bitrate (e.g., "128k", "192k", "320k")
        
    Returns:
        Dict with extraction result
    """
    from .media import ffmpeg_execute
    
    bridge = get_bridge()
    bridge.log(f"Extracting audio from {input_path}...")
    
    # Validate input
    if not os.path.exists(input_path):
        raise ToolError(f"Input file does not exist: {input_path}")
    
    # Ensure output has correct extension
    if not output_path.lower().endswith(f".{format}"):
        output_path = f"{os.path.splitext(output_path)[0]}.{format}"
    
    # Use ffmpeg_process tool
    result = ffmpeg_execute(
        input_path=input_path,
        output_path=output_path,
        operation="extract_audio",
        params={"format": format, "bitrate": bitrate}
    )
    
    return {
        "success": True,
        "input": input_path,
        "output": output_path,
        "format": format,
        "bitrate": bitrate,
        "duration_seconds": result.get("media_duration_seconds", 0),
        "message": f"Audio extracted: {output_path}"
    }


def trim_audio(
    input_path: str,
    output_path: str,
    start: str,
    end: Optional[str] = None,
    duration: Optional[str] = None
) -> Dict:
    """
    Trim audio file.
    
    Args:
        input_path: Input audio file path
        output_path: Output audio file path
        start: Start time (e.g., "00:00:10" or "10" for seconds)
        end: End time (optional, use duration instead if preferred)
        duration: Duration to keep (optional, use end instead if preferred)
        
    Returns:
        Dict with trim result
    """
    from .media import ffmpeg_execute
    
    bridge = get_bridge()
    bridge.log(f"Trimming audio from {start}...")
    
    if not os.path.exists(input_path):
        raise ToolError(f"Input file does not exist: {input_path}")
    
    if end is None and duration is None:
        raise ToolError("Either 'end' or 'duration' must be specified")
    
    params = {"start": start}
    if end:
        params["end"] = end
    if duration:
        params["duration"] = duration
    
    result = ffmpeg_execute(
        input_path=input_path,
        output_path=output_path,
        operation="trim",
        params=params
    )
    
    return {
        "success": True,
        "input": input_path,
        "output": output_path,
        "start": start,
        "end": end,
        "duration": duration,
        "message": f"Audio trimmed: {output_path}"
    }


def merge_audio(
    input_paths: List[str],
    output_path: str,
    transition: str = "none"
) -> Dict:
    """
    Merge multiple audio files.
    
    Args:
        input_paths: List of input audio file paths
        output_path: Output audio file path
        transition: Transition type (none, crossfade)
        
    Returns:
        Dict with merge result
    """
    from .media import ffmpeg_execute
    
    bridge = get_bridge()
    
    if len(input_paths) < 2:
        raise ToolError("At least 2 input files required for merge")
    
    # Validate all inputs exist
    for path in input_paths:
        if not os.path.exists(path):
            raise ToolError(f"Input file does not exist: {path}")
    
    bridge.log(f"Merging {len(input_paths)} audio files...")
    
    # For simple concat (no transition)
    if transition == "none":
        # Create concat file for ffmpeg
        output_dir = os.path.dirname(output_path) or "."
        concat_file = os.path.join(output_dir, "concat_list.txt")
        
        with open(concat_file, "w") as f:
            for path in input_paths:
                # Use absolute paths
                abs_path = os.path.abspath(path)
                f.write(f"file '{abs_path}'\n")
        
        try:
            result = ffmpeg_execute(
                input_path=concat_file,
                output_path=output_path,
                operation="custom",
                params={
                    "args": "-f concat -safe 0 -c copy"
                }
            )
            
            # Clean up concat file
            os.remove(concat_file)
            
            return {
                "success": True,
                "inputs": input_paths,
                "output": output_path,
                "transition": transition,
                "message": f"Audio files merged: {output_path}"
            }
        except Exception as e:
            # Clean up on error
            if os.path.exists(concat_file):
                os.remove(concat_file)
            raise e
    
    else:
        raise ToolError(f"Transition '{transition}' not implemented yet")


def change_speed(
    input_path: str,
    output_path: str,
    speed: float
) -> Dict:
    """
    Change audio playback speed.
    
    Args:
        input_path: Input audio file path
        output_path: Output audio file path
        speed: Speed multiplier (0.5 = half speed, 2.0 = double speed)
        
    Returns:
        Dict with speed change result
    """
    from .media import ffmpeg_execute
    
    bridge = get_bridge()
    
    if not os.path.exists(input_path):
        raise ToolError(f"Input file does not exist: {input_path}")
    
    if speed < 0.25 or speed > 4.0:
        raise ToolError("Speed must be between 0.25 and 4.0")
    
    bridge.log(f"Changing speed to {speed}x...")
    
    # atempo filter supports 0.5 to 2.0, chain for extreme values
    if speed < 0.5:
        # Multiple slow filters
        stages = int(0.5 / speed) + 1
        actual_speed = speed ** (1 / stages)
        af_filter = f"atempo={actual_speed}"
        for _ in range(stages - 1):
            af_filter = f"{af_filter},atempo={actual_speed}"
    elif speed > 2.0:
        # Multiple tempo filters
        stages = int(speed / 2) + 1
        actual_speed = speed ** (1 / stages)
        af_filter = f"atempo={actual_speed}"
        for _ in range(stages - 1):
            af_filter = f"{af_filter},atempo={actual_speed}"
    else:
        af_filter = f"atempo={speed}"
    
    result = ffmpeg_execute(
        input_path=input_path,
        output_path=output_path,
        operation="filter",
        params={"af": af_filter}
    )
    
    return {
        "success": True,
        "input": input_path,
        "output": output_path,
        "speed": speed,
        "message": f"Audio speed changed to {speed}x: {output_path}"
    }


def change_pitch(
    input_path: str,
    output_path: str,
    semitones: float
) -> Dict:
    """
    Change audio pitch.
    
    Args:
        input_path: Input audio file path
        output_path: Output audio file path
        semitones: Pitch shift in semitones (positive = higher, negative = lower)
        
    Returns:
        Dict with pitch change result
    """
    from .media import ffmpeg_execute
    
    bridge = get_bridge()
    
    if not os.path.exists(input_path):
        raise ToolError(f"Input file does not exist: {input_path}")
    
    if semitones < -24 or semitones > 24:
        raise ToolError("Pitch shift must be between -24 and 24 semitones")
    
    bridge.log(f"Changing pitch by {semitones} semitones...")
    
    # rubberband pitch filter
    af_filter = f"rubberband=pitch={2 ** (semitones / 12)}"
    
    result = ffmpeg_execute(
        input_path=input_path,
        output_path=output_path,
        operation="filter",
        params={"af": af_filter}
    )
    
    return {
        "success": True,
        "input": input_path,
        "output": output_path,
        "semitones": semitones,
        "message": f"Audio pitch changed by {semitones} semitones: {output_path}"
    }


def normalize_audio(
    input_path: str,
    output_path: str,
    target_db: float = -16.0
) -> Dict:
    """
    Normalize audio volume.
    
    Args:
        input_path: Input audio file path
        output_path: Output audio file path
        target_db: Target loudness in dB (default -16 for LUFS)
        
    Returns:
        Dict with normalization result
    """
    from .media import ffmpeg_execute
    
    bridge = get_bridge()
    
    if not os.path.exists(input_path):
        raise ToolError(f"Input file does not exist: {input_path}")
    
    bridge.log(f"Normalizing audio to {target_db}dB...")
    
    # Loudnorm filter for EBU R128 normalization
    af_filter = f"loudnorm=I={target_db}:TP=-1.5:LRA=11"
    
    result = ffmpeg_execute(
        input_path=input_path,
        output_path=output_path,
        operation="filter",
        params={"af": af_filter}
    )
    
    return {
        "success": True,
        "input": input_path,
        "output": output_path,
        "target_db": target_db,
        "message": f"Audio normalized to {target_db}dB: {output_path}"
    }


def get_audio_info(input_path: str) -> Dict:
    """
    Get detailed audio file information.
    
    Args:
        input_path: Audio file path
        
    Returns:
        Dict with audio information
    """
    from .media import ffprobe_json
    
    bridge = get_bridge()
    
    if not os.path.exists(input_path):
        raise ToolError(f"File does not exist: {input_path}")
    
    bridge.log(f"Getting audio info for {input_path}...")
    
    # Use ffprobe to get audio stream info
    probe_result = ffprobe_json(
        input_path,
        show_streams=True,
        show_format=True
    )
    
    audio_stream = None
    for stream in probe_result.get("streams", []):
        if stream.get("codec_type") == "audio":
            audio_stream = stream
            break
    
    if not audio_stream:
        raise ToolError("No audio stream found in file")
    
    format_info = probe_result.get("format", {})
    
    return {
        "success": True,
        "path": input_path,
        "duration_seconds": float(format_info.get("duration", 0)),
        "format": format_info.get("format_name", "unknown"),
        "codec": audio_stream.get("codec_name", "unknown"),
        "sample_rate": audio_stream.get("sample_rate", "unknown"),
        "channels": audio_stream.get("channels", 0),
        "bitrate": format_info.get("bit_rate", "unknown"),
        "size_bytes": int(format_info.get("size", 0))
    }


def convert_audio_format(
    input_path: str,
    output_path: str,
    format: str,
    quality: str = "high"
) -> Dict:
    """
    Convert audio to different format.
    
    Args:
        input_path: Input audio file path
        output_path: Output audio file path
        format: Target format (mp3, m4a, wav, flac, ogg, opus)
        quality: Quality preset (low, medium, high, lossless)
        
    Returns:
        Dict with conversion result
    """
    from .media import ffmpeg_execute
    
    bridge = get_bridge()
    
    if not os.path.exists(input_path):
        raise ToolError(f"Input file does not exist: {input_path}")
    
    # Ensure correct extension
    if not output_path.lower().endswith(f".{format}"):
        output_path = f"{os.path.splitext(output_path)[0]}.{format}"
    
    bridge.log(f"Converting to {format} ({quality})...")
    
    # Quality presets
    quality_settings = {
        "mp3": {
            "low": "-q:a 7",
            "medium": "-Q:a 4",
            "high": "-q:a 2",
            "lossless": "-q:a 0"
        },
        "m4a": {
            "low": "-b:a 96k",
            "medium": "-b:a 128k",
            "high": "-b:a 256k",
            "lossless": "-b:a 320k"
        },
        "flac": {
            "low": "",
            "medium": "",
            "high": "",
            "lossless": ""  # FLAC is always lossless
        },
        "wav": {
            "low": "",
            "medium": "",
            "high": "",
            "lossless": ""  # WAV is always lossless
        },
        "ogg": {
            "low": "-q:a 1",
            "medium": "-q:a 3",
            "high": "-q:a 5",
            "lossless": "-q:a 10"
        },
        "opus": {
            "low": "-b:a 64k",
            "medium": "-b:a 128k",
            "high": "-b:a 192k",
            "lossless": "-b:a 256k"
        }
    }
    
    if format not in quality_settings:
        raise ToolError(f"Unsupported format: {format}")
    
    settings = quality_settings[format].get(quality, "")
    
    params = {"args": f"-c:a {format} {settings}".strip()} if settings else {}
    
    result = ffmpeg_execute(
        input_path=input_path,
        output_path=output_path,
        operation="convert",
        params={"codec": format, "quality": quality}
    )
    
    return {
        "success": True,
        "input": input_path,
        "output": output_path,
        "format": format,
        "quality": quality,
        "message": f"Audio converted to {format}: {output_path}"
    }
