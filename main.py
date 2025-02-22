from math import cos, pi, sqrt, ceil

from kandinsky import set_pixel

import time

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

class JpegDecoder:
    idct_table = [[cos((pi / 8) * (p + 0.5) * n) * (1 / sqrt(2) if n == 0 else 1) for n in range(8)] for p in range(8)]
    def __init__(self, buffer: bytes) -> None:
        self.buffer: bytes = buffer
        self.bit_pos: int = 0
        self.components = {}
        self.huffman_tables: dict[int, list[int]] = {}
        self.quant_tables: dict[int, bytes] = {}
        self.sampling = [0, 0]
        self.width = 0
        self.height = 0

        self.decode()

    def get_bit(self) -> bool:
        byte = self.buffer[self.bit_pos // 8]
        bit: bool = bool((byte >> (7 - self.bit_pos % 8)) & 1)
        self.bit_pos += 1
        return bit

    def read_bit(self, nbits: int) -> int:
        result = 0
        for _ in range(nbits):
            result = (result << 1) + self.get_bit()
        return result

    def define_huffman_table(self):
        self._skip(2) # Table length
        table_info = self._read(1)
                    
        lengths = [self._read(1) for _ in range(16)]
        elements = []
        for byte_length in lengths:
            elements += (self._read(1) for _ in range(byte_length))

        table = create_huffman_tree(lengths, elements)
        self.huffman_tables[table_info] = table

    def define_quantization_table(self):
        self._skip(2) # Table length
        table_info = self._read(1)
        qt_data = self._read(64, False)
        self.quant_tables[table_info] = qt_data

    def parse_frame_header(self):
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

    def parse_scan_header(self):
        self._skip(2) # Header size
        nb_components = self._read(1)
        for _ in range(nb_components):
            component_id = self._read(1)
            self.components[component_id]["DC"] = self._peak(1) >> 4
            self.components[component_id]["AC"] = self._read(1) & 0xF

        self._skip(3)

    def parse_scan(self):
        self._remove_ff()
        
        old_y_coeff = old_cb_coeff = old_cr_coeff = 0

        for y in range(ceil(self.height / (8 * self.sampling[1]))):
            for x in range(ceil(self.width / (8 * self.sampling[0]))):
                start = time.monotonic()
                mat_ys = []
                for i in range(self.sampling[0] * self.sampling[1]):
                    mat_y, old_y_coeff = self._build_matrix(self.components[1], old_y_coeff)
                    mat_ys.append(mat_y)

                mat_cb, old_cb_coeff = self._build_matrix(self.components[2], old_cb_coeff)
                mat_cr, old_cr_coeff = self._build_matrix(self.components[3], old_cr_coeff)
                end = time.monotonic()
                print(f"MCU computed in: {end - start:.3f}s")
                self.update_output(x, y, mat_ys, mat_cb, mat_cr)

    def update_output(self, x, y, mat_ys, mat_cb, mat_cr):
        for i in range(len(mat_ys)):
            for yy in range(8):
                for xx in range(8):
                    global_x = xx + 8 * (i % self.sampling[0])
                    global_y = yy + 8 * (i // self.sampling[1])

                    out_x = x * (8 * self.sampling[0]) + global_x
                    out_y = y * (8 * self.sampling[1]) + global_y

                    if out_y >= self.height:
                        break # End of scan (padding values)

                    cb_cr_x = global_x // self.sampling[0]
                    cb_cr_y = global_y // self.sampling[1]
                    c = self._YCbCr_to_rgb(
                        mat_ys[i][xx][yy],
                        mat_cb[cb_cr_x][cb_cr_y],
                        mat_cr[cb_cr_x][cb_cr_y]
                    )

                    set_pixel(out_x, out_y, c)

    def decode(self) -> None:
        while True: 
            marker: int = self._read(2)
            if marker == 0xFFD8: # Start Of Image
                pass
            elif marker == 0xFFD9: # End Of Image
                return
            else:
                if marker == 0xFFDA: # Start Of Scan
                    self.parse_scan_header()
                    self.parse_scan()

                elif marker == 0xFFC4:
                    self.define_huffman_table()
                
                elif marker == 0xFFDB:
                    self.define_quantization_table()

                elif marker == 0xFFC0: # Start Of Frame
                    self.parse_frame_header()

                else:
                    chunk_length = self._peak(2)
                    self._skip(chunk_length)

            if self.bit_pos // 8 >= len(self.buffer):
                break

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

    def _remove_ff(self):
        new_buffer = bytes()
        while True:
            current_byte = self._read(1, False)

            if current_byte == b'\xFF':
                next_byte = self._peak(1)

                if next_byte == 0x00:
                    new_buffer += current_byte
                    self._skip(1)
                else: break

            else: new_buffer += current_byte

        self.buffer = new_buffer
        self.bit_pos = 0
    
    def _get_category(self, huffman_tree: list) -> int:
        result = huffman_tree

        while isinstance(result, list):
            result = result[self.get_bit()]

        return result
    
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
                            coeffs[n1 * 8 + n2]
                            * self.idct_table[y][n2]
                            * self.idct_table[x][n1]
                            )
                        
                output[y][x] = round(coeff / 4) + 128

        return output

    def _build_matrix(self, component, old_dc_coeff):
        quant = self.quant_tables[component["quant_mapping"]]

        category = self._get_category(self.huffman_tables[component["DC"]])
        bits = self.read_bit(category)
        dc_coeff = self._decode_number(category, bits) + old_dc_coeff
        
        result = [0] * 64
        result[0] = dc_coeff * quant[0]
        i = 1
        while i < 64:
            category = self._get_category(self.huffman_tables[16 + component["AC"]])
            if category == 0: break

            if category > 15:
                i += category >> 4
                category &= 0x0F

            bits = self.read_bit(category)
            
            coeff = self._decode_number(category, bits)
            result[i] = coeff * quant[i]
            i += 1

        result = self._zigzag(result)
        result = self._idct(result)
        return result, dc_coeff

    def _read(self, nbytes: int, to_int: bool = True) -> bytes | int:
        """
        Read a block of data from the buffer and returns it
        """
        pos = self.bit_pos // 8
        data = self.buffer[pos : pos + nbytes]
        self.bit_pos += nbytes * 8
        return self._from_bytes(data) if to_int else data
    
    def _peak(self, nbytes: int, to_int: bool = True, offset: int = 0) -> bytes | int:
        """
        Same as the _read method but doesn't change the _pos attribute
        """
        pos = self.bit_pos // 8
        data = self.buffer[pos + offset : pos + offset + nbytes]
        return self._from_bytes(data) if to_int else data

    def _skip(self, nbytes: int) -> None:
        """
        Skip a number of bytes of the buffer
        """
        self.bit_pos += nbytes * 8

from out import buffer
JpegDecoder(buffer)