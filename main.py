from PIL import Image
from io import BytesIO
import math

NUMWORKS_SIZE = 320, 222

def create_jpeg_pyfile(filepath: str, output_file_name: str) -> bytes:
    """
    This function takes an image path and scale it to the numworks viewport size.
    It then convert and compress the image into a jpeg file and write the image's byte into a python file.
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
        img.save(output, "Jpeg",
                 quality=50,
                 optimize=True)
        
        #print(output.tell())
        #Image.open(output).show()
        
        with open(output_file_name, "w") as out_file:
            out_file.write("buffer = " + str(output.getvalue()))

class IDCT:
    """
    An Inverse Discrete Cosine Transformation Class
    """
    def __init__(self):
        self.base = bytearray([0] * 64)
        self.zigzag: list[bytes] = [
            b'\x00\x01\x05\x06\x0e\x0f\x1b\x1c',
            b'\x02\x04\x07\r\x10\x1a\x1d*',
            b'\x03\x08\x0c\x11\x19\x1e)+',
            b'\t\x0b\x12\x18\x1f(,5',
            b"\n\x13\x17 '-46",
            b'\x14\x16!&.37<',
            b'\x15"%/28;=',
            b'#$019:>?'
        ]
        self.idct_precision = 8
        self.idct_table = [
            [
                (self._norm_coeff(u) * math.cos(((2.0 * x + 1.0) * u * math.pi) / 16.0))
                for x in range(self.idct_precision)
            ]
            for u in range(self.idct_precision)
        ]
    
    @staticmethod
    def _norm_coeff(n: int) -> float:
        return 1.0 / math.sqrt(2.0) if n == 0 else 1.0
    
    def rearrange(self) -> list[bytes]:
        for x in range(8):
            for y in range(8):
                self.zigzag[x][y] = self.base[self.zigzag[x][y]]

        return self.zigzag

    def compute(self):
        out = [bytearray(range(8)) for i in range(8)]
        for x in range(8):
            for y in range(8):
                local_sum = 0
                for u in range(self.idct_precision):
                    for v in range(self.idct_precision):
                        local_sum += (
                            self.zigzag[v][u]
                            * self.idct_table[u][x]
                            * self.idct_table[v][y]
                        )

                out[y][x] = local_sum // 4

        self.base = out

class HuffmanTable:
    def __init__(self, lengths: list[int], elements: list[int]):
        self.tree = []
        self._init_tree(lengths, elements)

    @staticmethod
    def _bits_from_lengths(root: list | int, element: int, pos: int) -> bool:
        """
        Code from https://github.com/aguaviva/micro-jpeg-visualizer
        """
        if isinstance(root, list):
            if pos == 0:
                if len(root) < 2:
                    root.append(element)
                    return True                
                return False

            for i in [0, 1]:
                if len(root) == i:
                    root.append([])

                if HuffmanTable._bits_from_lengths(root[i], element, pos - 1):
                    return True

        return False

    def _init_tree(self, lengths: list[int], elements: list[int]) -> None:
        """
        Code from https://github.com/aguaviva/micro-jpeg-visualizer
        """
        element_idx = 0
        for i in range(len(lengths)):
            for _ in range(lengths[i]):
                self._bits_from_lengths(self.tree, elements[element_idx], i)
                element_idx += 1


class JpegDecoder:
    markers = {
        0xFFD8: "SOI",  # Start Of Image
        0xFFE0: "APP0", # Application specific header
        0xFFC0: "SOF0", # Start of Frame
        0xFFC4: "DHT",  # Define Huffman Table
        0xFFDB: "DQT",  # Define Quantization Table
        0xFFDD: "DRI",  # Define Restart Interval
        0xFFDA: "SOS",  # Start Of Scan
        0xFFFE: "COM",  # Comment
        0xFFD9: "EOI"  # End of Image
    }

    def __init__(self, buffer: bytes) -> None:
        self.buffer: bytes = buffer
        self._pos: int = 0
        self.huffman_tables: dict[int, HuffmanTable] = {}
        self.quant_tables: dict[int, bytes] = {}
        self.quant_mapping: bytes = b''
        self.width = 0
        self.height = 0

        self.log_markers()

    @staticmethod
    def _from_bytes(data: bytes) -> int:
        """
        Returns the integer value of the given byte data.
        It is needed because the numworks runs on python 3.4 and it doesn't implement the `self._from_bytes` method
        """
        result = 0
        for byte in data:
            result = (result << 8) | byte
        return result
    
    def _build_matrix(self, idx, quant, old_dc_coeff):
        i = IDCT()


    
    def _remove_ff00(self):
        new_buffer = bytearray(self.buffer[:self._pos])

        while True:
            if self._peak(1) == 0xff:
                if self._peak(1, offset=1) != 0:
                    new_buffer.append(self._read(1))
                    new_buffer.append(self._read(1))
                    break # Reached end of image
                new_buffer.append(self._read(1))
                self._skip(1)
            else:
                new_buffer.append(self._read(1))

        self.buffer = bytes(new_buffer)

    def log_markers(self) -> None:
        while True: 
            marker = self.markers.get(self._read(2), "NULL")
            print(marker)
            if marker == "SOI":
                pass
            elif marker == "EOI":
                return
            else:
                if marker == "SOS":
                    self._remove_ff00()
                    IDCT()
                    old_lum_dc_coeff, old_cb_dc_coeff, old_cr_dc_coeff = 0, 0, 0
                    for y in range(self.height // 8):
                        for x in range(self.width // 8):
                            pass

                    self._goto(2, False)
                elif marker == "DHT":
                    self._skip(2) # Table length
                    table_info = self._read(1)
                    
                    lengths = [self._read(1) for _ in range(16)]

                    elements = []
                    for byte_length in lengths:
                        elements += (self._read(1) for _ in range(byte_length))
                    
                    self.huffman_tables[table_info] = HuffmanTable(lengths, elements)
                
                elif marker == "DQT":
                    self._skip(2) # Table length
                    table_info = self._read(1)
                    qt_data = self._read(64, False)
                    self.quant_tables[table_info] = qt_data

                elif marker == "SOF0":
                    self._skip(2) # Table length
                    self._skip(1)
                    #data_precision = self._read(1)
                    self.height = self._read(2)
                    self.width = self._read(2)
                    nb_components = self._read(1)

                    for i in range(nb_components):
                        self._skip(2)
                        #component_id = self._read(1)
                        #sampling_factor = self._read(1)
                        quant_tb_nb = self._read(1, False)
                        self.quant_mapping += quant_tb_nb

                else:
                    chunk_length = self._peak(2)
                    self._skip(chunk_length)

            if self._pos >= len(self.buffer):
                break

    def _goto(self, position: int, from_start: bool = True) -> None:
        """
        Change the _pos attribute relative to start or end of the buffer
        """
        self._pos = position if from_start else len(self.buffer) - position

    def _read(self, nbytes: int, to_int: bool = True) -> bytes | int:
        """
        Read a block of data from the buffer and returns it
        """
        data = self.buffer[self._pos : self._pos + nbytes]
        self._pos += nbytes
        return self._from_bytes(data) if to_int else data
    
    def _peak(self, nbytes: int, to_int: bool = True, offset: int = 0) -> bytes | int:
        """
        Same as the _read method but doesn't change the _pos attribute
        """
        data = self.buffer[self._pos + offset : self._pos + offset + nbytes]
        return self._from_bytes(data) if to_int else data

    def _skip(self, nbytes: int) -> None:
        """
        Skip a number of bytes of the buffer
        """
        self._pos += nbytes

img_bytes = create_jpeg_pyfile("images/python.png", "out.py")
from out import buffer
decoder = JpegDecoder(buffer)