import binascii
import gzip
import struct

output = b''

#####

# names
fac_names = b''

fac_names += struct.pack(">H", 0)   # offset
fac_names += b'test\x00'

# have to compress now, rip
fac_names_comp = gzip.compress(fac_names)

#####

# geometry
fac_geom = b''

fac_geom += struct.pack(">IIII", 0, 1, 0, 0)

# have to compress now, rip
fac_geom_comp = gzip.compress(fac_geom)

#####

# header
output += struct.pack('>H', 0x565A)     # hdrid
output += struct.pack('>H', 0x0001)     # version
output += struct.pack('>B', 32)         # granule size

output += struct.pack(">I", 1)                      # numfacs
output += struct.pack(">I", 0xdeadbeef)             # numfacbytes
output += struct.pack(">I", 100)                    # longestname
output += struct.pack(">I", len(fac_names_comp))    # zfacnamesize
output += struct.pack(">I", len(fac_names))         # zfacname_predec_size
output += struct.pack(">I", len(fac_geom_comp))     # zfacgeometrysize
output += struct.pack(">b", -9)                     # timescale

output += fac_names_comp
output += fac_geom_comp

#####

def varint(x):
    x0 = x & 0x7F
    x >>= 7
    if not x:
        x0 |= 0x80
    output = x0.to_bytes(1)
    while x:
        xn = x & 0x7F
        x >>= 7
        if not x:
            xn |= 0x80
        output += xn.to_bytes(1)
    return output

# block
block_data = b''

block_data += varint(4)                 # num_time_ticks
block_data += varint(10)
block_data += varint(5)
block_data += varint(10)
block_data += varint(15)

block_data += varint(1)                 # num_sections

block_data += varint(4)                 # num_dict_entries
if len(block_data) % 4:
    block_data += b'\xaa' * (4 - (len(block_data) % 4))
# waveforms here
block_data += struct.pack("<I", 0b1110)
block_data += struct.pack("<I", 0b0100)
block_data += struct.pack("<I", 0b1000)
block_data += struct.pack("<I", 0b0010)

block_data += b'\x01'                   # num_bitplanes
if len(block_data) % 4:
    block_data += b'\xaa' * (4 - (len(block_data) % 4))
# vindex table here
block_data += struct.pack("<I", 0)
block_data += struct.pack("<I", 2)
block_data += struct.pack("<I", 1)
block_data += struct.pack("<I", 3)

block_data += varint(0)                 # num_str_entries

print(binascii.hexlify(block_data))

block_compr = gzip.compress(block_data)

#####

output += struct.pack(">IIQQ",
                      len(block_data),  # uncompressed size
                      len(block_compr), # compressed size
                      0,                # start time
                      100)              # end time
output += block_compr

#####

with open('mlt4.vzt', 'wb') as f:
    f.write(output)
