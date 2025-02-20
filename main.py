from PIL import Image
from io import BytesIO
import numpy as np
from math import cos, pi, sqrt

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

def bits_from_lengths(root: list | int, element: int, pos: int) -> bool:
    """
    Recursive function that is used to create an huffman tree list
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

            if bits_from_lengths(root[i], element, pos - 1):
                return True

    return False

def create_huffman_tree(lengths: list[int], elements: list[int]) -> list[int]:
    """
    Create a list that represent an huffman tree
    Code from https://github.com/aguaviva/micro-jpeg-visualizer
    """
    tree = []

    element_idx = 0
    for i in range(len(lengths)):
        for _ in range(lengths[i]):
            bits_from_lengths(tree, elements[element_idx], i)
            element_idx += 1

    return tree

class BitStream:
    def __init__(self, buffer: bytes):
        self.buffer = buffer
        self._pos = 0

    def get_bit(self) -> bool:
        byte = self.buffer[self._pos // 8]
        bit: bool = bool((byte >> (7 - self._pos % 8)) & 1)
        self._pos += 1
        return bit

    def read(self, nbits: int) -> int:
        result = 0
        for _ in range(nbits):
            result = (result << 1) + self.get_bit()
        return result 

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

    idct_table = [[ cos((pi / 8) * (n + 0.5) * k) for n in range(8) ] for k in range(8) ]

    def __init__(self, buffer: bytes) -> None:
        self.buffer: bytes = buffer
        self._pos: int = 0
        self.components = {}
        self.huffman_tables: dict[int, list[int]] = {}
        self.quant_tables: dict[int, bytes] = {}
        self.sampling = [0, 0]
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
    
    @staticmethod
    def _decode_number(code, bits):
        l = 2 ** (code - 1)
        return bits if bits >= l else bits - (2 * l - 1)
    
    @staticmethod
    def _zigzag(coeffs):
        zigzag = [
            0, 1, 5, 6, 14, 15, 27, 28,
            2, 4, 7, 13, 16, 26, 29, 42,
            3, 8, 12, 17, 25, 30, 41, 43,
            9, 11, 18, 24, 31, 40, 44, 53,
            10, 19, 23, 32, 39, 45, 52, 54,
            20, 22, 33, 38, 46, 51, 55, 60,
            21, 34, 37, 47, 50, 56, 59, 61,
            35, 36, 48, 49, 57, 58, 62, 63,
        ]

        for i in range(64):
            zigzag[i] = coeffs[zigzag[i]]

        return zigzag

    def _get_scan(self):
        new_buffer = bytearray()

        while True:
            current_byte = self._read(1)

            if current_byte == 0xFF:
                next_byte = self._peak(1)

                if next_byte == 0x00:
                    new_buffer.append(current_byte)
                    self._skip(1)
                else: break

            else: new_buffer.append(current_byte)

        return bytes(new_buffer)
    
    def _get_category(self, huffman_tree: list, stream: BitStream) -> int:
        result = huffman_tree

        while isinstance(result, list):
            result = result[stream.get_bit()]

        return result
    
    @staticmethod
    def _get_norm(x):
        return 1 / sqrt(2) if x == 0 else 1
    
    @staticmethod
    def _YCbCr_to_rgb(Y: int, Cb: int, Cr: int) -> tuple[int, int, int]:
        r = Y + 1.402 * (Cr - 128)
        g = Y - 0.34414 * (Cb - 128) - 0.714136 * (Cr - 128)
        b = Y + 1.772 * (Cb - 128)
        
        r = max(0, min(255, round(r)))
        g = max(0, min(255, round(g)))
        b = max(0, min(255, round(b)))

        return (r, g, b)

    def _idct(self, coeffs):
        output = [[0 for _ in range(8)] for _ in range(8)]
        for y in range(8):
            for x in range(8):
                coeff = 0
                for n1 in range(8):
                    for n2 in range(8):
                        coeff += (
                            self._get_norm(n1) * self._get_norm(n2)
                            * coeffs[n1 * 8 + n2]
                            * cos((pi / 8) * (y + 0.5) * n2)
                            * cos((pi / 8) * (x + 0.5) * n1)
                            )
                        
                output[y][x] = round(coeff / 4) + 128

        return output

    def _build_matrix(self, component, stream: BitStream, old_dc_coeff):
        quant = self.quant_tables[component["quant_mapping"]]

        category = self._get_category(self.huffman_tables[component["DC"]], stream)
        bits = stream.read(category)
        dc_coeff = self._decode_number(category, bits) + old_dc_coeff
        
        result = [0] * 64
        result[0] = dc_coeff * quant[0]
        i = 1
        while i < 64:
            category = self._get_category(self.huffman_tables[16 + component["AC"]], stream)
            if category == 0: break

            if category > 15:
                i += category >> 4
                category &= 0x0F

            bits = stream.read(category)
            
            coeff = self._decode_number(category, bits)
            result[i] = coeff * quant[i]
            i += 1

        result = self._zigzag(result)
        result = self._idct(result)
        return result, dc_coeff

    def log_markers(self) -> None:
        while True: 
            marker = self.markers.get(self._read(2), "NULL")
            if marker == "SOI":
                pass
            elif marker == "EOI":
                return
            else:
                if marker == "SOS":
                    self._skip(2) # Header size
                    nb_components = self._read(1)
                    for _ in range(nb_components):
                        component_id = self._read(1)
                        self.components[component_id]["DC"] = self._peak(1) >> 4
                        self.components[component_id]["AC"] = self._read(1) & 0xF

                    self._skip(3)
                    stream = BitStream(self._get_scan())
                    
                    old_y_coeff = old_cb_coeff = old_cr_coeff = 0

                    output = np.zeros((self.height, self.width, 3), dtype=np.uint8)

                    for y in range(self.height // (8 * self.sampling[1])):
                        for x in range(self.width // (8 * self.sampling[0])):
                            mat_ys = []
                            for i in range(self.sampling[0] * self.sampling[1]):
                                mat_y, old_y_coeff = self._build_matrix(self.components[1], stream, old_y_coeff)
                                mat_ys.append(mat_y)

                            mat_cb, old_cb_coeff = self._build_matrix(self.components[2], stream, old_cb_coeff)
                            mat_cr, old_cr_coeff = self._build_matrix(self.components[3], stream, old_cr_coeff)

                            for i in range(len(mat_ys)):
                                for yy in range(8):
                                    for xx in range(8):

                                        global_x = xx + 8 * (i % self.sampling[0])
                                        global_y = yy + 8 * (i // self.sampling[1])

                                        cb_cr_x = global_x // self.sampling[0]
                                        cb_cr_y = global_y // self.sampling[1]
                                        c = self._YCbCr_to_rgb(
                                            mat_ys[i][xx][yy],
                                            mat_cb[cb_cr_x][cb_cr_y],
                                            mat_cr[cb_cr_x][cb_cr_y]
                                        )
                                        
                                        out_x = x * (8 * self.sampling[0]) + global_x
                                        out_y = y * (8 * self.sampling[1]) + global_y
                                        
                                        output[out_y][out_x] = c

                    Image.fromarray(output).show()
                    self._goto(2, False)

                elif marker == "DHT":
                    self._skip(2) # Table length
                    table_info = self._read(1)
                    
                    lengths = [self._read(1) for _ in range(16)]
                    elements = []
                    for byte_length in lengths:
                        elements += (self._read(1) for _ in range(byte_length))

                    table = create_huffman_tree(lengths, elements)
                    self.huffman_tables[table_info] = table
                
                elif marker == "DQT":
                    self._skip(2) # Table length
                    table_info = self._read(1)
                    qt_data = self._read(64, False)
                    self.quant_tables[table_info] = qt_data

                elif marker == "SOF0":
                    self._skip(3) # Table length and data precision
                    self.height = self._read(2)
                    self.width = self._read(2)
                    nb_components = self._read(1)
                    
                    for _ in range(nb_components):
                        component_id = self._read(1)
                        self.sampling[0] = max(self.sampling[0], self._peak(1) >> 4)
                        self.sampling[1] = max(self.sampling[1], self._read(1) & 0xF)
                        component = {
                            "quant_mapping": self._read(1)
                        }
                        self.components[component_id] = component

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

#img_bytes = create_jpeg_pyfile("images/sunset.png", "out.py")
from out import buffer
decoder = JpegDecoder(buffer)