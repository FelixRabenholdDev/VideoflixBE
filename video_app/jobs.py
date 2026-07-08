import subprocess

from video_app.utils import build_hls_output_dir
from video_app.models import Video

RESOLUTIONS = ["480p", "720p", "1080p"]

RESOLUTION_DIMENSIONS = {
    "480p": "854x480",
    "720p": "1280x720",
    "1080p": "1920x1080",
}


def convert_video_to_hls(video_id):
    """RQ job: converts the uploaded video into multiple HLS resolutions."""    

    video = Video.objects.get(id=video_id)
    for resolution in RESOLUTIONS:
        output_dir = build_hls_output_dir(video_id, resolution)
        _convert_single_resolution(video.video_file.path, output_dir, resolution)


def _convert_single_resolution(source_path, output_dir, resolution):
    """Run the FFMPEG conversion for a single resolution. (Implement using FFMPEG's HLS docs.)"""

    manifest_path = output_dir / "index.m3u8"
    cmd = _build_ffmpeg_command(source_path, manifest_path, output_dir, resolution)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFMPEG failed for {resolution}: {result.stderr}")

def _build_ffmpeg_command(source_path, manifest_path, output_dir, resolution):
    """Build the FFMPEG command as an argument list for a given resolution."""
    
    dimensions = RESOLUTION_DIMENSIONS[resolution]
    return [
        "ffmpeg", "-i", source_path,
        "-s", dimensions,
        "-c:v", "libx264", "-crf", "23",
        "-c:a", "aac", "-strict", "-2",
        "-hls_time", "10",
        "-hls_playlist_type", "vod",
        "-hls_segment_filename", str(output_dir / "segment_%03d.ts"),
        str(manifest_path),
    ]