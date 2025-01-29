from PIL import Image
from io import BytesIO
from typing import Literal

NUMWORKS_SIZE = 320, 222

def create_webp_pyfile(filepath: str, output_file_name: str) -> bytes:
    """
    This function takes an image path and scale it to the numworks viewport size.
    It then convert and compress the image into a webp file and write the image's byte into a python file.
    Returns the bytes saved.
    """
    with Image.open(filepath) as img:
        img = img.crop(img.getbbox()) # Crop the image to the actual bounding box

        # Rescale the image so it fits into the calculator but keep the aspect ratio
        scale_factor = min(NUMWORKS_SIZE[1] / img.height, 1) # Take the minimum to not upscale the image
        img = img.convert("RGB").resize((round(img.width * scale_factor),
                                            round(img.height * scale_factor)))
        
        img = img.resize(NUMWORKS_SIZE)
        
        output = BytesIO()
        img.save(output, "WebP",
                 lossless=False,
                 quality=20,
                 alpha_quality=0,
                 method=6)
        
        with open(output_file_name, "w") as out_file:
            out_file.write("buffer = " + str(output.getvalue()))

class ByteReader:
    def __init__(self, buffer: bytes, as_big_endian: bool = True):
        self.buffer = buffer
        self._pos = 0
        self._endianness = as_big_endian # True for big endian

    def read(self, nbytes: int, as_big_endian: bool | None = None) -> bytes:
        """
        Read a block of data from the buffer and returns it
        """
        data = self.buffer[self._pos : self._pos + nbytes]
        self._pos += nbytes

        if as_big_endian is None:
            as_big_endian = self._endianness

        return data if as_big_endian else data[::-1]
    
    def skip(self, nbytes: int) -> None:
        self._pos += nbytes

def decode_webp_bytes(buffer: bytes):
    reader = ByteReader(buffer, False)
    # -- Webp file header --
    reader.skip(4)
    file_size = int.from_bytes(reader.read(4))
    reader.skip(4)
    file_format: Literal["VP8 ", "VP8L"] = reader.read(4, True).decode()
    print(file_format)

img_bytes = create_webp_pyfile("images/python.png", "out.py")
from out import buffer
decode_webp_bytes(buffer)