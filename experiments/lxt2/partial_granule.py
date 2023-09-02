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

#####

# geometry
fac_geom = b''

fac_geom += struct.pack(">IIII", 0, 7, 0, 0)
fac_geom += struct.pack(">IIII", 0, 7, 0, 0)

#####

# header
output += struct.pack('>H', 0x1380)     # hdrid
output += struct.pack('>H', 0x0001)     # version
output += struct.pack('>B', 64)         # granule size

output += struct.pack(">I", 2)              # numfacs
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

partial_data = b''
partial_data += struct.pack(">B", 19)     # num_time_table_entries
partial_data += struct.pack(">Q", 5)
partial_data += struct.pack(">Q", 10)
partial_data += struct.pack(">Q", 15)
partial_data += struct.pack(">Q", 20)
partial_data += struct.pack(">Q", 25)
partial_data += struct.pack(">Q", 30)
partial_data += struct.pack(">Q", 35)
partial_data += struct.pack(">Q", 40)
partial_data += struct.pack(">Q", 45)
partial_data += struct.pack(">Q", 50)
partial_data += struct.pack(">Q", 55)
partial_data += struct.pack(">Q", 60)
partial_data += struct.pack(">Q", 65)
partial_data += struct.pack(">Q", 70)
partial_data += struct.pack(">Q", 75)
partial_data += struct.pack(">Q", 80)
partial_data += struct.pack(">Q", 85)
partial_data += struct.pack(">Q", 90)
partial_data += struct.pack(">Q", 95)
partial_data += struct.pack(">B", 1)      # fac_map_index_width
partial_data += struct.pack(">B", 0)
partial_data += struct.pack(">B", 1)      # fac_curpos_width
partial_data += b'\x00'
partial_data += b'\x0f'
partial_data += b'\x10'
partial_data += b'\x01'
partial_data += b'\x03'
partial_data += b'\x04'
partial_data += b'\x02'
partial_data += b'\x06'
partial_data += b'\x05'
partial_data += b'\x0a'
partial_data += b'\x09'
partial_data += b'\x08'
partial_data += b'\x07'
partial_data += b'\x0e'
partial_data += b'\x0d'
partial_data += b'\x0c'
partial_data += b'\x0b'
partial_data += b'\x11'
partial_data += b'\x12'

block_data += b'\x02'                   # LXT2_RD_GRAN_SECT_TIME_PARTIAL
block_data += struct.pack(">I", 1)      # start fac idx
block_data += struct.pack(">I", len(partial_data))
block_data += partial_data

block_data += b'\x01'                   # LXT2_RD_GRAN_SECT_DICT
# dict
dict_data = b''
dict_data += b'lolhi\x00'
block_data += dict_data
# map
block_data += struct.pack(">Q", 0x7FFFF)
block_data += struct.pack(">I", 1)              # num_dict_entries
block_data += struct.pack(">I", len(dict_data)) # dict_size
block_data += struct.pack(">I", 1)              # num_map_entries

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

with open('partial_granule.lxt2', 'wb') as f:
    f.write(output)
