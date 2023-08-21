"""Implementation of the KNX date data point."""
from __future__ import annotations

from typing import NamedTuple

from xknx.exceptions import ConversionError

from .dpt import DPTBase
from .payload import DPTArray, DPTBinary


class XYYColor(NamedTuple):
    """
    Representation of XY color with brightness.

    `color`: tuple(x-axis, y-axis) each 0..1; None if invalid.
    `brightness`: int 0..255; None if invalid.
    tuple(tuple(float, float) | None, int | None)
    """

    color: tuple[float, float] | None = None
    brightness: int | None = None


class DPTColorXYY(DPTBase):
    """Abstraction for KNX 6 octet color xyY (DPT 242.600)."""

    payload_type = DPTArray
    payload_length = 6

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> XYYColor:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)

        x_axis_int = raw[0] << 8 | raw[1]
        y_axis_int = raw[2] << 8 | raw[3]
        brightness = raw[4]

        color_valid = raw[5] >> 1 & 0b1
        brightness_valid = raw[5] & 0b1

        return XYYColor(
            color=(
                # round to 5 digits for better readability but still preserving precision
                round(x_axis_int / 0xFFFF, 5),
                round(y_axis_int / 0xFFFF, 5),
            )
            if color_valid
            else None,
            brightness=brightness if brightness_valid else None,
        )

    @classmethod
    def to_knx(
        cls, value: XYYColor | tuple[tuple[float, float] | None, int | None]
    ) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        try:
            if not isinstance(value, XYYColor):
                value = XYYColor(*value)
            color_valid = False
            brightness_valid = False
            x_axis, y_axis, brightness = 0, 0, 0

            if value.color is not None:
                for _ in (axis for axis in value.color if not 0 <= axis <= 1):
                    raise ValueError
                color_valid = True
                x_axis, y_axis = (round(axis * 0xFFFF) for axis in value.color)

            if value.brightness is not None:
                if not 0 <= value.brightness <= 255:
                    raise ValueError
                brightness_valid = True
                brightness = int(value.brightness)

            return DPTArray(
                (
                    x_axis >> 8,
                    x_axis & 0xFF,
                    y_axis >> 8,
                    y_axis & 0xFF,
                    brightness,
                    color_valid << 1 | brightness_valid,
                )
            )
        except (ValueError, TypeError):
            raise ConversionError(f"Could not serialize {cls.__name__}", value=value)

class DPTColorRGB(DPTBase):
    """Abstraction for KNX 6 octet color RGB (DPT 242.600)."""

    value_type = "ColorRGB"
    payload_type = DPTArray
    payload_length = 3

    @classmethod
    def to_knx(self, value: Sequence[int]) -> DPTArray:
        """Convert value to payload."""
        if not isinstance(value, (list, tuple)):
            raise ConversionError(
                "Could not serialize RemoteValueColorRGB (wrong type)",
                value=value,
                type=type(value),
            )
        if len(value) != 3:
            raise ConversionError(
                "Could not serialize DPT 232.600 (wrong length)",
                value=value,
                type=type(value),
            )
        if (
            any(not isinstance(color, int) for color in value)
            or any(color < 0 for color in value)
            or any(color > 255 for color in value)
        ):
            raise ConversionError(
                "Could not serialize DPT 232.600 (wrong bytes)", value=value
            )

        return DPTArray(list(value))
        
    @classmethod
    def from_knx(self, payload: DPTArray | DPTBinary) -> tuple[int, int, int]:
        """Convert current payload to value."""
        if not (isinstance(payload, DPTArray) and len(payload.value) == 3):
            raise CouldNotParseTelegram("Payload invalid", payload=str(payload))

        return payload.value[0], payload.value[1], payload.value[2]
