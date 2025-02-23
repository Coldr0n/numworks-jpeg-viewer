from math import cos, pi, sqrt, ceil

from kandinsky import set_pixel

def create_huffman_tree(lengths: list[int], elements: list[int]) -> list[int]:
    """
    Create a list that represent an huffman binary tree
    Code from https://github.com/aguaviva/micro-jpeg-visualizer
    """
    tree = []

    element_idx = 0
    for i in range(len(lengths)):
        for _ in range(lengths[i]):
            bits_from_lengths(tree, elements[element_idx], i)
            element_idx += 1

    return tree

def bits_from_lengths(root: list | int, element: int, pos: int) -> bool:
    """
    Recursive function that is used to create an huffman binary tree
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

def bytes_to_int(data: bytes) -> int:
    """
    Returns the integer value of the given byte data.
    It is needed because Micropython doesn't implement the `int.bytes_to_int()` method
    """
    result = 0
    for byte in data:
        result = (result << 8) | byte # Make space for the next byte and adds it
    return result

def decode_number(category: int, bits: int) -> int:
    """
    Decodes the right coefficient given a category and bits. 
    """
    l: int = 2 ** (category - 1)
    return bits if bits >= l else bits - (l * 2 - 1)

def YCbCr_to_rgb(Y: int, Cb: int, Cr: int) -> tuple[int, int, int]:
    """
    Converts a YCbCr value to rgb
    """
    r = Y + 1.402 * (Cr - 128)
    g = Y - 0.34414 * (Cb - 128) - 0.714136 * (Cr - 128)
    b = Y + 1.772 * (Cb - 128)
    # Clamping the values
    r = max(0, min(255, round(r)))
    g = max(0, min(255, round(g)))
    b = max(0, min(255, round(b)))

    return (r, g, b)

class JpegDecoder:
    def __init__(self, buffer: bytes) -> None:
        """
        Create a JpegDecoder object and decode a jpeg file buffer.
        The buffer size should be around 5KB
        """
        self.buffer: bytes = buffer
        self.bit_pos: int = 0
        self.components: dict[int, dict[bytes, int]] = {} # Stores info about the components
        self.huffman_tables: dict[int, list[int]] = {}
        self.quant_tables: dict[int, bytes] = {}
        self.sampling = [0, 0]
        self.width = 0
        self.height = 0
        self.idct_table: list[list[int]] = []

        self.read_markers()
        
    def read_markers(self) -> None:
        """
        This methods reads every marker of the file and exectute the appropriate methods
        """
        while True: 
            marker = self.read(2)
            if marker == 0xFFD8: pass # Start Of Image
            elif marker == 0xFFD9:
                break # End Of Image

            elif marker == 0xFFC4: self.define_huffman_table()
            elif marker == 0xFFDB: self.define_quantization_table()

            elif marker == 0xFFC0:
                self.parse_frame_header() # Start Of Frame

            elif marker == 0xFFDA: # Start Of Scan
                self.parse_scan_header()
                self.scan()

            else: self.skip(self.peak(2)) # Skip the section

            # Breaks the loop if there is no data left after reading a section
            if self.bit_pos // 8 >= len(self.buffer): break

    def define_huffman_table(self) -> None:
        """
        Define Huffman Table (DHT) section.
        This method reads the data to create a Huffman binary tree and adds it to a dictionary.
        """
        self.skip(2) # Table length
        table_info: int = self.read(1)
                    
        lengths: int = [self.read(1) for _ in range(16)]
        elements: list[int] = []
        for byte_length in lengths:
            elements += [self.read(1) for _ in range(byte_length)]

        self.huffman_tables[table_info] = create_huffman_tree(lengths, elements)

    def define_quantization_table(self) -> None:
        """
        Define Quantization Table (DQT) section.
        Reads the quantization table and adds it to a dictionnary
        """
        self.skip(2) # Table length
        table_info = self.read(1)
        qt_data = self.read(64, True)
        self.quant_tables[table_info] = qt_data

    def parse_frame_header(self) -> None:
        """
        Start Of Frame header (SOF0) section.
        Parses different information about the structure of the start of scan section
        """
        self.skip(3) # Table length and data precision
        self.height = self.read(2)
        self.width = self.read(2)
        nb_components = self.read(1)
        
        for _ in range(nb_components):
            component_id = self.read(1)
            self.sampling[0] = max(self.sampling[0], self.peak(1) >> 4)
            self.sampling[1] = max(self.sampling[1], self.read(1) & 0xF)
            self.components[component_id] = {b"quant_mapping": self.read(1)}

    def parse_scan_header(self) -> None:
        """
        Header of the Start Of Start (SOS) section.
        Parses and get more information about the SOS.
        """
        self.skip(2) # Header size
        nb_components = self.read(1)
        for _ in range(nb_components):
            component_id = self.read(1)
            self.components[component_id][b"DC"] = self.peak(1) >> 4 # Gets the DC table index
            self.components[component_id][b"AC"] = self.read(1) & 0xF # Gets the AC table index

        self.skip(3) # Meaningless data

    def scan(self) -> None:
        """
        Start Of Scan (SOS) section.
        Interpret and displays the actual image data that is inside the jpeg file
        """
        self.remove_ff00()

        # Precompute table for the inverse decrete cosine transform
        self.idct_table = [[cos((pi / 8) * (p + 0.5) * n) * (1 / sqrt(2) if n == 0 else 1) for n in range(8)] for p in range(8)]

        old_y_coeff = old_cb_coeff = old_cr_coeff = 0

        samplings = self.sampling[0] * self.sampling[1]

        # This loop runs for every MCU of the file
        for y in range(ceil(self.height / (8 * self.sampling[1]))):
            for x in range(ceil(self.width / (8 * self.sampling[0]))):
                y_mats = []
                for _ in range(samplings):
                    y_mat, old_y_coeff = self.build_matrix(self.components[1], old_y_coeff)
                    y_mats.append(y_mat)

                cb_mat, old_cb_coeff = self.build_matrix(self.components[2], old_cb_coeff)
                cr_mat, old_cr_coeff = self.build_matrix(self.components[3], old_cr_coeff)
                
                self.display_pixels(x, y, y_mats, cb_mat, cr_mat)

    def display_pixels(self, x: int, y: int,
                      y_mats: list[list[int]], cb_mat: list[list[int]], cr_mat: list[list[int]]) -> None:
        """
        Displays the pixels of the decoded matrices
        """
        block_width = 8 * self.sampling[0]
        block_height = 8 * self.sampling[1]

        for i in range(len(y_mats)):
            i_x = i % self.sampling[0]
            i_y = i // self.sampling[0]

            for yy in range(8):
                global_block_y = i_y * 8 + yy # Relative position inside of all the mcus
                pixel_y = y * block_height + global_block_y # Absolute pixel position

                if pixel_y >= self.height: break # Padding values out of bound

                for xx in range(8):
                    global_block_x = i_x * 8 + xx
                    pixel_x = x * block_width + global_block_x
                    
                    if pixel_x >= self.width: break # Padding values out of bound

                    # Indices for the Cb or Cr matrices
                    sampled_x = global_block_x // self.sampling[0]
                    sampled_y = global_block_y // self.sampling[1]

                    color = YCbCr_to_rgb(y_mats[i][xx][yy], 
                                         cb_mat[sampled_x][sampled_y],
                                         cr_mat[sampled_x][sampled_y])
                    set_pixel(pixel_x, pixel_y, color)

    def build_matrix(self, component: list[int], old_dc_coeff: int) -> tuple[list[list[int]], int]:
        """
        Reads data to build entirely the 8 * 8 matrix of a component.
        It decodes the DC and AC coeffs, dequantize them, rearange the values, and perform an idct.
        """
        quant_table = self.quant_tables[component[b"quant_mapping"]]

        category = self.read_category(self.huffman_tables[component[b"DC"]])
        bits = self.read_bits(category)
        dc_coeff = decode_number(category, bits) + old_dc_coeff
        
        result = [0] * 64
        result[0] = dc_coeff * quant_table[0]
        i = 1
        ac_huffman_table = self.huffman_tables[16 + component[b"AC"]]
        while i < 64:
            category = self.read_category(ac_huffman_table)
            if category == 0: break

            i += category >> 4
            category &= 0x0F

            if i >= 64:
                break

            bits = self.read_bits(category)
            coeff = decode_number(category, bits)
            result[i] = coeff * quant_table[i]
            i += 1

        result = self.rearange_coeffs(result)
        result = self.idct(result)
        return result, dc_coeff
    
    def idct(self, coeffs: list[int]) -> list[list[int]]:
        """
        Computes the Inverse Discrete Cosine Transform and shifts back the transformed value by 128
        """
        output = [[0] * 8 for _ in range(8)]
        for y in range(8):
            for x in range(8):
                # Precomputes the tables for given x and y coordinates
                idct_y = [self.idct_table[y][n2] for n2 in range(8)]
                idct_x = [self.idct_table[x][n1] for n1 in range(8)]

                coeff: int = 0
                for n1 in range(8):
                    global_n1 = n1 * 8
                    for n2 in range(8):
                        coeff += coeffs[global_n1 + n2] * idct_y[n2] * idct_x[n1]

                output[y][x] = round(coeff / 4) + 128

        return output
        
    def rearange_coeffs(self, coeffs: list[int]) -> list[int]:
        """
        Changes the order of the coefficients to be in a zigzag order
        """
        zigzag = [ # Initial indices
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

    def remove_ff00(self) -> None:
        """
        This method undoes byte stuffing.
        It removes the 0x00 byte after every 0xff that is present is the scan data.
        """
        new_buffer = bytes()
        while True:
            current_byte = self.read(1, True)

            if current_byte == b'\xff':
                next_byte = self.peak(1)

                if next_byte == 0x00:
                    new_buffer += current_byte
                    self.skip(1)
                else: break # Breaking when another marker is encoutered (End Of Image)

            else: new_buffer += current_byte

        self.buffer = new_buffer
        self.bit_pos = 0

    def read_category(self, huffman_tree: list) -> int:
        """
        Returns the next category of the buffer using the passed Huffman tree
        """
        result = huffman_tree

        while isinstance(result, list):
            result = result[self.get_bit()]

        return result

    def read(self, nbytes: int, to_bytes: bool = False) -> bytes | int:
        """
        Reads a block of data from the file buffer, returns it as an integer or bytes and removes the read part from the buffer.
        """
        data = self.buffer[:nbytes]
        self.buffer = self.buffer[nbytes:]
        return data if to_bytes else bytes_to_int(data)
    
    def peak(self, nbytes: int, to_bytes: bool = False) -> bytes | int:
        """
        Reads a block of data from the file buffer, returns it as an integer or bytes and doesn't change the buffer data.
        """
        data = self.buffer[:nbytes]
        return data if to_bytes else bytes_to_int(data)

    def skip(self, nbytes: int) -> None:
        """
        Skip a number of bytes of the buffer
        """
        self.buffer = self.buffer[nbytes:]

    def get_bit(self) -> int:
        """
        Returns the value of the next bit of the buffer
        """
        byte = self.buffer[self.bit_pos >> 3]
        bit = (byte >> (7 - self.bit_pos & 0x07)) & 1
        self.bit_pos += 1
        return bit

    def read_bits(self, nbits: int) -> int:
        """
        Reads n bits from the buffer and returns the final value
        """
        result = 0
        for _ in range(nbits):
            result = (result << 1) | self.get_bit()
        return result

from out import buffer
JpegDecoder(buffer)