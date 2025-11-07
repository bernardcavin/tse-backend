import base64
import dataclasses as dc
import hashlib
import hmac
from typing import Any, Dict, Literal, Optional, Sequence, Union
from urllib.parse import quote


@dc.dataclass
class ImgProxy:
    """Complete imgproxy URL generator supporting all processing options."""

    # Source configuration
    source_url: str = ""
    s3_bucket: str = ""
    s3_object: str = ""
    proxy_host: Optional[str] = None

    # Authentication
    key: Optional[str] = dc.field(default=None, repr=False)
    salt: Optional[str] = dc.field(default=None, repr=False)

    # Basic resize options (meta-option: resize/rs)
    resizing_type: Literal["fit", "fill", "fill-down", "force", "auto"] = "fit"
    width: int = 0
    height: int = 0
    enlarge: bool = False
    extend: bool = False

    # Gravity
    gravity: Union[
        Literal["no", "so", "ea", "we", "noea", "nowe", "soea", "sowe", "ce", "sm"], str
    ] = "ce"
    gravity_x_offset: int = 0
    gravity_y_offset: int = 0

    # Size constraints
    min_width: int = 0
    min_height: int = 0
    zoom: float = 1.0
    dpr: float = 1.0

    # Cropping
    crop_width: float = 0
    crop_height: float = 0
    crop_gravity: Optional[str] = None

    # Image adjustments
    auto_rotate: bool = False
    rotate: int = 0
    background: Optional[str] = None
    background_alpha: float = 1.0

    # Color adjustments (Pro features)
    brightness: int = 0
    contrast: float = 1.0
    saturation: float = 1.0

    # Filters
    blur: float = 0
    sharpen: float = 0
    pixelate: int = 0

    # Watermark
    watermark_opacity: float = 0
    watermark_position: str = "ce"
    watermark_x_offset: int = 0
    watermark_y_offset: int = 0
    watermark_scale: float = 0
    watermark_url: str = ""
    watermark_text: str = ""

    # Quality and format
    quality: int = 0
    format_extension: str = ""
    max_bytes: int = 0

    # Metadata
    strip_metadata: bool = False
    keep_copyright: bool = False
    strip_color_profile: bool = False

    # Advanced options
    presets: Sequence[str] = dc.field(default_factory=list)
    advanced_options: Sequence[str] = dc.field(default_factory=list)
    cache_buster: str = ""
    expires: int = 0
    filename: str = ""
    return_attachment: bool = False

    # Processing control
    skip_processing: Sequence[str] = dc.field(default_factory=list)
    raw: bool = False

    @classmethod
    def from_s3(cls, bucket: str, object_key: str, **kwargs):
        """Create ImgProxy instance for S3 source."""
        return cls(s3_bucket=bucket, s3_object=object_key, **kwargs)

    @classmethod
    def from_url(cls, url: str, **kwargs):
        """Create ImgProxy instance for HTTP/HTTPS source."""
        return cls(source_url=url, **kwargs)

    def __post_init__(self):
        """Initialize signature options."""
        if not (self.source_url or (self.s3_bucket and self.s3_object)):
            raise ValueError(
                "Either source_url or both s3_bucket and s3_object must be provided"
            )

        try:
            self.key: Union[bytes, Literal[False]] = self.key and bytes.fromhex(
                self.key
            )
            self.salt: Union[bytes, Literal[False]] = self.salt and bytes.fromhex(
                self.salt
            )
        except ValueError:
            raise ValueError(
                "Invalid signature parameters - key and salt must be hex-encoded"
            )

    def _add_option(self, parts: list, option: str, *values, condition: bool = True):
        """Helper to add processing options."""
        if condition and any(str(v) for v in values):
            parts.append(f"{option}:{':'.join(str(v) for v in values)}")

    def _build_processing_options(self, **runtime_options) -> list:
        """Build the processing options list."""
        parts = []

        # Presets first
        if self.presets:
            parts.append(f"pr:{':'.join(self.presets)}")

        # Advanced options
        parts.extend(self.advanced_options)

        # Resize (meta-option) - rs:type:width:height:enlarge:extend
        if self.width or self.height or self.resizing_type != "fit":
            enlarge_val = 1 if self.enlarge else 0
            extend_val = 1 if self.extend else 0
            parts.append(
                f"rs:{self.resizing_type}:{self.width}:{self.height}:{enlarge_val}:{extend_val}"
            )

        # Size constraints
        self._add_option(parts, "mw", self.min_width, condition=self.min_width > 0)
        self._add_option(parts, "mh", self.min_height, condition=self.min_height > 0)

        # Zoom and DPR
        self._add_option(parts, "z", self.zoom, condition=self.zoom != 1.0)
        self._add_option(parts, "dpr", self.dpr, condition=self.dpr != 1.0)

        # Gravity
        if self.gravity != "ce" or self.gravity_x_offset or self.gravity_y_offset:
            parts.append(
                f"g:{self.gravity}:{self.gravity_x_offset}:{self.gravity_y_offset}"
            )

        # Cropping
        if self.crop_width or self.crop_height:
            crop_gravity = self.crop_gravity or self.gravity
            parts.append(f"c:{self.crop_width}:{self.crop_height}:{crop_gravity}")

        # Rotation
        self._add_option(
            parts, "ar", 1 if self.auto_rotate else 0, condition=self.auto_rotate
        )
        self._add_option(parts, "rot", self.rotate, condition=self.rotate != 0)

        # Background
        if self.background:
            parts.append(f"bg:{self.background}")
            if self.background_alpha != 1.0:
                parts.append(f"bga:{self.background_alpha}")

        # Color adjustments
        if self.brightness != 0 or self.contrast != 1.0 or self.saturation != 1.0:
            parts.append(f"a:{self.brightness}:{self.contrast}:{self.saturation}")

        # Filters
        self._add_option(parts, "bl", self.blur, condition=self.blur > 0)
        self._add_option(parts, "sh", self.sharpen, condition=self.sharpen > 0)
        self._add_option(parts, "pix", self.pixelate, condition=self.pixelate > 0)

        # Watermark
        if self.watermark_opacity > 0:
            wm_parts = [self.watermark_opacity]
            if any(
                [
                    self.watermark_position != "ce",
                    self.watermark_x_offset,
                    self.watermark_y_offset,
                    self.watermark_scale,
                ]
            ):
                wm_parts.extend(
                    [
                        self.watermark_position,
                        self.watermark_x_offset,
                        self.watermark_y_offset,
                        self.watermark_scale,
                    ]
                )
            parts.append(f"wm:{':'.join(str(p) for p in wm_parts)}")

        if self.watermark_url:
            encoded_url = (
                base64.urlsafe_b64encode(self.watermark_url.encode())
                .decode()
                .rstrip("=")
            )
            parts.append(f"wmu:{encoded_url}")

        if self.watermark_text:
            encoded_text = (
                base64.urlsafe_b64encode(self.watermark_text.encode())
                .decode()
                .rstrip("=")
            )
            parts.append(f"wmt:{encoded_text}")

        # Quality and format
        self._add_option(parts, "q", self.quality, condition=self.quality > 0)
        if self.format_extension:
            parts.append(f"f:{self.format_extension}")
        self._add_option(parts, "mb", self.max_bytes, condition=self.max_bytes > 0)

        # Metadata options
        if self.strip_metadata:
            parts.append("sm:1")
        if self.keep_copyright:
            parts.append("kcr:1")
        if self.strip_color_profile:
            parts.append("scp:1")

        # Processing control
        if self.skip_processing:
            parts.append(f"skp:{':'.join(self.skip_processing)}")
        if self.raw:
            parts.append("raw:1")

        # Cache and meta
        if self.cache_buster:
            parts.append(f"cb:{self.cache_buster}")
        if self.expires:
            parts.append(f"exp:{self.expires}")
        if self.filename:
            encoded_filename = (
                base64.urlsafe_b64encode(self.filename.encode()).decode().rstrip("=")
            )
            parts.append(f"fn:{encoded_filename}:1")
        if self.return_attachment:
            parts.append("att:1")

        # Add runtime options
        for key, value in runtime_options.items():
            if isinstance(value, (list, tuple)):
                parts.append(f"{key}:{':'.join(str(v) for v in value)}")
            else:
                parts.append(f"{key}:{value}")

        return parts

    def _build_source_url(self) -> str:
        """Build the source URL part."""
        if self.source_url:
            # Plain HTTP/HTTPS URL
            escaped_url = quote(self.source_url, safe=":/?#[]@!$&'()*+,;=")
            source_part = f"plain/{escaped_url}"
        else:
            # S3 URL
            source_part = f"plain/s3://{self.s3_bucket}/{self.s3_object}"

        # Add extension for plain URLs
        if self.format_extension:
            source_part += f"@{self.format_extension}"

        return source_part

    def _calculate_signature(self, path: str) -> str:
        """Calculate HMAC signature for the path."""
        if not (self.key and self.salt):
            return "insecure"

        message = self.salt + path.encode("utf-8")
        digest = hmac.new(self.key, msg=message, digestmod=hashlib.sha256).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

    def build_url(self, **options) -> str:
        """Build the complete imgproxy URL."""
        # Build processing options
        processing_parts = self._build_processing_options(**options)

        # Build source URL
        source_part = self._build_source_url()

        # Construct the path (what gets signed)
        if processing_parts:
            path = f"/{'/'.join(processing_parts)}/{source_part}"
        else:
            path = f"/{source_part}"

        # Calculate signature
        signature = self._calculate_signature(path)

        # Build final URL
        final_path = f"/{signature}{path}"

        if self.proxy_host:
            return f"{self.proxy_host.rstrip('/')}{final_path}"
        return final_path

    def __call__(self, **options) -> str:
        """Generate URL (shorthand for build_url)."""
        return self.build_url(**options)

    def __str__(self) -> str:
        """String representation returns the URL."""
        return self.build_url()
