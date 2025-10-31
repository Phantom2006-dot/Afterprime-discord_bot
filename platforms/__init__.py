from .linkedin import LinkedInPlatform
from .meta import MetaPlatform
from .tiktok import TikTokPlatform

PLATFORMS = {
    'linkedin': LinkedInPlatform,
    'meta': MetaPlatform,
    'instagram': MetaPlatform,
    'tiktok': TikTokPlatform
}

def get_platform(platform_name):
    platform_class = PLATFORMS.get(platform_name)
    if not platform_class:
        raise ValueError(f"Unsupported platform: {platform_name}")
    return platform_class()
