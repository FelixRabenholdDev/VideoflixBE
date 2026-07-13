from pathlib import Path

from django.conf import settings

ALLOWED_RESOLUTIONS = {"480p", "720p", "1080p"}


def build_manifest_path(movie_id, resolution):
    """Build the filesystem path to a video's HLS manifest for the given resolution."""
    return Path(settings.MEDIA_ROOT) / "hls" / str(movie_id) / resolution / "index.m3u8"

def build_hls_output_dir(video_id, resolution):
    """Build the filesystem directory where converted HLS files for a resolution should be stored."""
    output_dir = Path(settings.MEDIA_ROOT) / "hls" / str(video_id) / resolution
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def is_valid_resolution(resolution):
    """Check whether the requested resolution is supported."""
    return resolution in ALLOWED_RESOLUTIONS

def build_segment_path(movie_id, resolution, segment):
    """Build the filesystem path to a single HLS segment, guarding against path traversal."""
    output_dir = Path(settings.MEDIA_ROOT) / "hls" / str(movie_id) / resolution
    segment_path = (output_dir / segment).resolve()
    if output_dir.resolve() not in segment_path.parents:
        return None
    return segment_path