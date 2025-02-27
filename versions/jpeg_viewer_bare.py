from math import cos, pi, sqrt, ceil

from kandinsky import set_pixel

def create_huffman_tree(lengths, elements):
    tree = []
    element_idx = 0
    for i in range(len(lengths)):
        for _ in range(lengths[i]):
            bits_from_lengths(tree, elements[element_idx], i)
            element_idx += 1
    return tree

def bits_from_lengths(root, element, pos):
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

def bytes_to_int(data):
    result = 0
    for byte in data:
        result = (result << 8) | byte 
    return result

def decode_number(category, bits):
    l = 2 ** (category - 1)
    return bits if bits >= l else bits - (l * 2 - 1)

def YCbCr_to_rgb(Y, Cb, Cr):
    r = Y + 1.402 * (Cr - 128)
    g = Y - 0.34414 * (Cb - 128) - 0.714136 * (Cr - 128)
    b = Y + 1.772 * (Cb - 128)
    r = max(0, min(255, round(r)))
    g = max(0, min(255, round(g)))
    b = max(0, min(255, round(b)))
    return (r, g, b)

class JpegViewer:
    def __init__(self, buffer):
        self.buffer = buffer
        self.bit_pos = 0
        self.components = {} 
        self.huffman_tables = {}
        self.quant_tables = {}
        self.sampling = [0, 0]
        self.width = self.height = 0
        self.idct_table = []

        self.read_markers()
        
    def read_markers(self):
        while True: 
            marker = self.read(2)
            if marker == 0xFFD8: pass 
            elif marker == 0xFFD9:
                break 
            elif marker == 0xFFC4: self.define_huffman_table()
            elif marker == 0xFFDB: self.define_quantization_table()
            elif marker == 0xFFC0:
                self.parse_frame_header() 
            elif marker == 0xFFDA: 
                self.parse_scan_header()
                self.scan()
            else: self.skip(self.read(2, peak=True)) 
            if self.bit_pos // 8 >= len(self.buffer): break

    def define_huffman_table(self):
        self.skip(2) 
        table_info = self.read(1)
        lengths = [self.read(1) for _ in range(16)]
        elements = []

        for byte_length in lengths:
            elements += [self.read(1) for _ in range(byte_length)]

        self.huffman_tables[table_info] = create_huffman_tree(lengths, elements)

    def define_quantization_table(self):
        self.skip(2) 
        table_info = self.read(1)
        qt_data = self.read(64, True)
        self.quant_tables[table_info] = qt_data

    def parse_frame_header(self):
        self.skip(3) 
        self.height = self.read(2)
        self.width = self.read(2)
        nb_components = self.read(1)

        for _ in range(nb_components):
            component_id = self.read(1)
            self.sampling[0] = max(self.sampling[0], self.read(1, peak=True) >> 4)
            self.sampling[1] = max(self.sampling[1], self.read(1) & 0xF)
            self.components[component_id] = {b"quant_mapping": self.read(1)}

    def parse_scan_header(self):
        self.skip(2) 
        nb_components = self.read(1)
        for _ in range(nb_components):
            component_id = self.read(1)
            self.components[component_id][b"DC"] = self.read(1, peak=True) >> 4 
            self.components[component_id][b"AC"] = self.read(1) & 0xF 

        self.skip(3) 

    def scan(self):
        self.idct_table = [[cos((pi / 8) * (p + 0.5) * n) * (1 / sqrt(2) if n == 0 else 1) for n in range(8)] for p in range(8)]

        old_y_coeff = old_cb_coeff = old_cr_coeff = 0
        samplings = self.sampling[0] * self.sampling[1]

        for y in range(ceil(self.height / (8 * self.sampling[1]))):
            for x in range(ceil(self.width / (8 * self.sampling[0]))):
                y_mats = []
                for _ in range(samplings):
                    y_mat, old_y_coeff = self.build_matrix(self.components[1], old_y_coeff)
                    y_mats.append(y_mat)

                cb_mat, old_cb_coeff = self.build_matrix(self.components[2], old_cb_coeff)
                cr_mat, old_cr_coeff = self.build_matrix(self.components[3], old_cr_coeff)
                
                self.display_pixels(x, y, y_mats, cb_mat, cr_mat)

    def display_pixels(self, x, y, y_mats, cb_mat, cr_mat):
        block_width = 8 * self.sampling[0]
        block_height = 8 * self.sampling[1]

        for i in range(len(y_mats)):
            i_x = i % self.sampling[0]
            i_y = i // self.sampling[0]

            for yy in range(8):
                global_block_y = i_y * 8 + yy 
                pixel_y = y * block_height + global_block_y 

                if pixel_y >= self.height: break 

                for xx in range(8):
                    global_block_x = i_x * 8 + xx
                    pixel_x = x * block_width + global_block_x
                    
                    if pixel_x >= self.width: break 

                    sampled_x = global_block_x // self.sampling[0]
                    sampled_y = global_block_y // self.sampling[1]

                    color = YCbCr_to_rgb(y_mats[i][xx][yy], 
                                         cb_mat[sampled_x][sampled_y],
                                         cr_mat[sampled_x][sampled_y])
                    set_pixel(pixel_x, pixel_y, color)

    def build_matrix(self, component, old_dc_coeff):
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
    
    def idct(self, coeffs):
        output = [[0] * 8 for _ in range(8)]
        for y in range(8):
            for x in range(8):
                idct_y = [self.idct_table[y][n2] for n2 in range(8)]
                idct_x = [self.idct_table[x][n1] for n1 in range(8)]

                coeff = 0
                for n1 in range(8):
                    global_n1 = n1 * 8
                    for n2 in range(8):
                        coeff += coeffs[global_n1 + n2] * idct_y[n2] * idct_x[n1]

                output[y][x] = round(coeff / 4) + 128

        return output
        
    def rearange_coeffs(self, coeffs):
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

    def read_category(self, huffman_tree):
        result = huffman_tree

        while isinstance(result, list):
            result = result[self.get_bit()]

        return result

    def read(self, nbytes, to_bytes=False, peak=False):
        pos = self.bit_pos // 8
        data = self.buffer[pos : pos + nbytes]
        if not peak: self.bit_pos += nbytes * 8
        return data if to_bytes else bytes_to_int(data)

    def skip(self, nbytes):
        self.bit_pos += nbytes * 8

    def get_bit(self):
        self.skip_ff00()

        byte = self.buffer[self.bit_pos >> 3]
        bit = (byte >> (7 - self.bit_pos & 0x07)) & 1
        self.bit_pos += 1
        return bit
    
    def skip_ff00(self):
        if (self.bit_pos & 0x07) == 0: 
            byte_pos = self.bit_pos >> 3

            if self.buffer[byte_pos] == 0x00 and self.buffer[byte_pos - 1] == 0xff:
                self.bit_pos += 8 

    def read_bits(self, nbits):
        result = 0
        for _ in range(nbits):
            result = (result << 1) | self.get_bit()
        return result

def open(buffer): JpegViewer(buffer)

if __name__ == '__main__':
    file_name = input("Enter the name of the python module where the image is located: ")
    try: open(__import__(file_name).b)
    except ModuleNotFoundError:
        print("Error: the module", file_name, "was not found")
    except AttributeError:
        print("Error: couldn't find the image data, it should be in a variable named 'b'")

    print("Program finished.")
