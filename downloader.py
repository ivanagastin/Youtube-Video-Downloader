import os
import threading
import yt_dlp

def format_bytes(bytes_count):
    if bytes_count is None or bytes_count == 0:
        return "N/A"
    bytes_count = float(bytes_count)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_count < 1024:
            return f"{bytes_count:.2f} {unit}"
        bytes_count /= 1024
    return f"{bytes_count:.2f} TB"

def format_speed(bytes_per_sec):
    if bytes_per_sec is None:
        return "N/A"
    return f"{format_bytes(bytes_per_sec)}/s"

def format_eta(seconds):
    if seconds is None:
        return "N/A"
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    seconds %= 60
    if minutes < 60:
        return f"{minutes}m {seconds}s"
    hours = minutes // 60
    minutes %= 60
    return f"{hours}h {minutes}m {seconds}s"

def is_ffmpeg_available():
    """Checks if ffmpeg is available in the system path."""
    import shutil
    return shutil.which("ffmpeg") is not None

class YouTubeDownloader:
    def __init__(self):
        self._current_download_thread = None
        self._stop_requested = False

    def fetch_video_info(self, url):
        """
        Fetches metadata and formats for a given YouTube URL.
        Runs synchronously (should be called in a background thread by the GUI).
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Extract basic info
                video_details = {
                    'title': info.get('title', 'Unknown Title'),
                    'thumbnail': info.get('thumbnail', ''),
                    'duration': format_eta(info.get('duration')),
                    'author': info.get('uploader', 'Unknown Channel'),
                    'views': f"{info.get('view_count', 0):,}",
                    'description': info.get('description', ''),
                    'url': url,
                    'formats_combined': [],
                    'formats_video_only': [],
                    'formats_audio_only': [],
                }
                
                # Parse formats
                formats = info.get('formats', [])
                seen_video_qualities = set()
                seen_audio_qualities = set()
                
                for f in formats:
                    f_id = f.get('format_id')
                    ext = f.get('ext', '')
                    vcodec = f.get('vcodec', 'none')
                    acodec = f.get('acodec', 'none')
                    
                    # Size calculation
                    size = f.get('filesize') or f.get('filesize_approx')
                    size_str = format_bytes(size) if size else "Unknown size"
                    
                    has_video = vcodec != 'none'
                    has_audio = acodec != 'none'
                    
                    # 1. Combined (Video + Audio)
                    if has_video and has_audio:
                        height = f.get('height')
                        resolution = f"{height}p" if height else f.get('resolution', 'Unknown')
                        fps = f.get('fps', '')
                        fps_str = f" @ {fps}fps" if fps and fps > 30 else ""
                        
                        video_details['formats_combined'].append({
                            'id': f_id,
                            'ext': ext,
                            'resolution': resolution,
                            'fps': fps,
                            'size_str': size_str,
                            'display_name': f"{resolution}{fps_str} ({ext}) - {size_str}"
                        })
                    
                    # 2. Video Only (requires ffmpeg to merge, or downloaded as silent)
                    elif has_video and not has_audio:
                        height = f.get('height')
                        if height:
                            resolution = f"{height}p"
                            fps = f.get('fps', '')
                            fps_str = f" @ {fps}fps" if fps and fps > 30 else ""
                            key = (resolution, ext, fps)
                            
                            if key not in seen_video_qualities:
                                seen_video_qualities.add(key)
                                video_details['formats_video_only'].append({
                                    'id': f_id,
                                    'ext': ext,
                                    'resolution': resolution,
                                    'fps': fps,
                                    'size_str': size_str,
                                    'display_name': f"{resolution}{fps_str} ({ext}) - {size_str} [No Audio]"
                                })
                                
                    # 3. Audio Only
                    elif not has_video and has_audio:
                        abr = f.get('abr')
                        bitrate = f"{int(abr)}kbps" if abr else "Unknown Bitrate"
                        key = (bitrate, ext)
                        
                        if key not in seen_audio_qualities:
                            seen_audio_qualities.add(key)
                            video_details['formats_audio_only'].append({
                                    'id': f_id,
                                    'ext': ext,
                                    'bitrate': bitrate,
                                    'size_str': size_str,
                                    'display_name': f"{bitrate} ({ext}) - {size_str}"
                                })

                # Sort lists for clean presentation
                # Sort combined by height/resolution desc
                def get_height(fmt):
                    res = fmt['resolution']
                    if 'p' in res:
                        try:
                            return int(res.replace('p', ''))
                        except ValueError:
                            pass
                    return 0
                
                video_details['formats_combined'].sort(key=get_height, reverse=True)
                video_details['formats_video_only'].sort(key=get_height, reverse=True)
                
                # Sort audio by bitrate desc
                def get_bitrate(fmt):
                    bitrate = fmt['bitrate']
                    if 'kbps' in bitrate:
                        try:
                            return int(bitrate.replace('kbps', ''))
                        except ValueError:
                            pass
                    return 0
                
                video_details['formats_audio_only'].sort(key=get_bitrate, reverse=True)
                
                return video_details
                
        except Exception as e:
            raise Exception(f"Failed to fetch video info: {str(e)}")

    def download(self, url, format_id, download_type, output_path, progress_callback, done_callback, error_callback):
        """
        Starts a background thread to download the video.
        """
        self._stop_requested = False
        self._current_download_thread = threading.Thread(
            target=self._download_worker,
            args=(url, format_id, download_type, output_path, progress_callback, done_callback, error_callback),
            daemon=True
        )
        self._current_download_thread.start()

    def cancel_download(self):
        self._stop_requested = True

    def _download_worker(self, url, format_id, download_type, output_path, progress_callback, done_callback, error_callback):
        def ydl_hook(d):
            if self._stop_requested:
                raise Exception("Download cancelled by user")
                
            if d['status'] == 'downloading':
                speed = d.get('speed')
                eta = d.get('eta')
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                
                percent = (downloaded / total) * 100 if total > 0 else 0
                
                progress_callback({
                    'status': 'downloading',
                    'percent': percent / 100.0, # scale to 0.0 - 1.0 for progress bar
                    'speed': format_speed(speed),
                    'eta': format_eta(eta),
                    'downloaded': format_bytes(downloaded),
                    'total': format_bytes(total),
                    'message': f"Downloading... {percent:.1f}% ({format_bytes(downloaded)} / {format_bytes(total)})"
                })
            elif d['status'] == 'finished':
                progress_callback({
                    'status': 'finished',
                    'percent': 1.0,
                    'speed': "0 B/s",
                    'eta': "0s",
                    'message': "Processing and saving file..."
                })

        # Set up options
        out_tmpl = os.path.join(output_path, '%(title)s.%(ext)s')
        
        ydl_opts = {
            'outtmpl': out_tmpl,
            'progress_hooks': [ydl_hook],
            'quiet': True,
            'no_warnings': True,
        }
        
        # Configure format
        if download_type == 'combined':
            # Pre-merged format, download directly
            ydl_opts['format'] = format_id
        elif download_type == 'video_only':
            # Video only, no merging needed unless converting format, download direct
            ydl_opts['format'] = format_id
        elif download_type == 'audio_only':
            # Audio only
            ydl_opts['format'] = format_id
            # If ffmpeg is available, let's convert to mp3 if requested (handled at higher level, or we just download as is)
            # We will download the direct audio format.
        elif download_type == 'best_merge':
            # This is "Merge Best Video + Best Audio" (requires ffmpeg)
            # format_id will contain video format, and we'll merge it with bestaudio
            if is_ffmpeg_available():
                ydl_opts['format'] = f"{format_id}+bestaudio/best"
                ydl_opts['merge_output_format'] = 'mp4'
            else:
                # Fallback to combined or warn
                error_callback("FFmpeg is required to merge high quality video and audio. Please choose a pre-merged format under 'Video + Audio' or install FFmpeg.")
                return

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # If we merged, the filename extension might have changed to mp4
                if download_type == 'best_merge':
                    base, _ = os.path.splitext(filename)
                    filename = base + ".mp4"
                
                # Check if file exists
                if os.path.exists(filename):
                    done_callback(filename)
                else:
                    # Let's search the output directory for matching titles if extension changed
                    title = info.get('title')
                    found = False
                    if title:
                        for f in os.listdir(output_path):
                            if title in f and f.endswith(('.mp4', '.mkv', '.webm', '.m4a', '.mp3')):
                                done_callback(os.path.join(output_path, f))
                                found = True
                                break
                    if not found:
                        done_callback(filename) # Fallback to default
        except Exception as e:
            if "Download cancelled" in str(e):
                error_callback("Download cancelled.")
            else:
                error_callback(f"Download error: {str(e)}")
