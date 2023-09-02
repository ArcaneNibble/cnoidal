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

fac_geom += struct.pack(">IIII", 0, 7, 0, 0)

#####

# header
output += struct.pack('>H', 0x1380)     # hdrid
output += struct.pack('>H', 0x0001)     # version
output += struct.pack('>B', 64)         # granule size

output += struct.pack(">I", 1)              # numfacs
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
block_data += struct.pack(">B", 19)     # num_time_table_entries
block_data += struct.pack(">Q", 5)
block_data += struct.pack(">Q", 10)
block_data += struct.pack(">Q", 15)
block_data += struct.pack(">Q", 20)
block_data += struct.pack(">Q", 25)
block_data += struct.pack(">Q", 30)
block_data += struct.pack(">Q", 35)
block_data += struct.pack(">Q", 40)
block_data += struct.pack(">Q", 45)
block_data += struct.pack(">Q", 50)
block_data += struct.pack(">Q", 55)
block_data += struct.pack(">Q", 60)
block_data += struct.pack(">Q", 65)
block_data += struct.pack(">Q", 70)
block_data += struct.pack(">Q", 75)
block_data += struct.pack(">Q", 80)
block_data += struct.pack(">Q", 85)
block_data += struct.pack(">Q", 90)
block_data += struct.pack(">Q", 95)
block_data += struct.pack(">B", 1)      # fac_map_index_width
block_data += struct.pack(">B", 0)
block_data += struct.pack(">B", 1)      # fac_curpos_width
block_data += b'\x00'
block_data += b'\x0f'
block_data += b'\x10'
block_data += b'\x01'
block_data += b'\x03'
block_data += b'\x04'
block_data += b'\x02'
block_data += b'\x06'
block_data += b'\x05'
block_data += b'\x0a'
block_data += b'\x09'
block_data += b'\x08'
block_data += b'\x07'
block_data += b'\x0e'
block_data += b'\x0d'
block_data += b'\x0c'
block_data += b'\x0b'
block_data += b'\x11'
block_data += b'\x12'

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

block_compr = gzip.compress(block_data)

output += struct.pack(">IIQQ",
                      len(block_data),  # uncompressed size
                      len(block_compr), # compressed size
                      0,                # start time
                      100)              # end time

# striped
output += struct.pack(">III",
                      len(block_compr), # compressed size
                      len(block_data),  # uncompressed size
                      0xFFFFFFFF)       # iter
output += block_compr

#####

with open('striped.lxt2', 'wb') as f:
    f.write(output)
