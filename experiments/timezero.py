import struct

output = b''

output += struct.pack('>H', 0x0138)     # hdrid
output += struct.pack('>H', 0x0004)     # version

#####

# LT_SECTION_FACNAME
facname_off = len(output)
output += struct.pack(">I", 1)  # numfacs
output += struct.pack(">I", 5)  # total memory

output += struct.pack(">H", 0)  # offset
output += b'test\x00'

#####

# LT_SECTION_FACNAME_GEOMETRY
facname_geom_off = len(output)
output += struct.pack(">IIII", 0, 0, 0, 0)

#####

# LT_SECTION_TIME_TABLE
time_table_off = len(output)
output += struct.pack(">I", 0)
output += struct.pack(">II", 0, 100)

#####

# LT_SECTION_SYNC_TABLE
sync_table_off = len(output)
output += struct.pack(">I", 0)

#####

# LT_SECTION_TIMEZERO
timezero_off = len(output)
output += struct.pack(">Q", 12345)

#####

output += b'\x00'                                       # LT_SECTION_END
output += struct.pack(">IB", facname_off, 3)            # LT_SECTION_FACNAME
output += struct.pack(">IB", facname_geom_off, 4)       # LT_SECTION_FACNAME_GEOMETRY
output += struct.pack(">IB", time_table_off, 6)         # LT_SECTION_TIME_TABLE
output += struct.pack(">IB", sync_table_off, 2)         # LT_SECTION_SYNC_TABLE
output += struct.pack(">IB", timezero_off, 20)          # LT_SECTION_TIMEZERO

output += b'\xB4'   # trlid

with open('timezero.lxt', 'wb') as f:
    f.write(output)
