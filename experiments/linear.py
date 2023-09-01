import struct

output = b''

output += struct.pack('>H', 0x0138)     # hdrid
output += struct.pack('>H', 0x0004)     # version

#####

# LT_SECTION_CHG
assert len(output) == 4
offs = []

offs.append(len(output))
output += b'\x02'   # fac
output += b'\x04'   # cmd -> 1

offs.append(len(output))
output += b'\x00'   # fac
output += b'\x05'   # cmd -> Z

offs.append(len(output))
output += b'\x00'   # fac
output += b'\x03'   # cmd -> 0

linear_chg_sz = len(output) - 4

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
output += struct.pack(">IIII", 0, 0xffffffff, 0xffffffff, 0)

#####

# LT_SECTION_TIME_TABLE
time_table_off = len(output)
output += struct.pack(">I", 3)
output += struct.pack(">II", 0, 100)

# pos delta
output += struct.pack(">I", offs[0])
output += struct.pack(">I", offs[1] - offs[0])
output += struct.pack(">I", offs[2] - offs[1])

# time delta
output += struct.pack(">I", 25)
output += struct.pack(">I", 25)
output += struct.pack(">I", 25)

#####

output += b'\x00'                                       # LT_SECTION_END
output += struct.pack(">IB", facname_off, 3)            # LT_SECTION_FACNAME
output += struct.pack(">IB", facname_geom_off, 4)       # LT_SECTION_FACNAME_GEOMETRY
output += struct.pack(">IB", time_table_off, 6)         # LT_SECTION_TIME_TABLE
output += struct.pack(">IB", linear_chg_sz, 15)         # LT_SECTION_ZCHG_PREDEC_SIZE

output += b'\xB4'   # trlid

with open('linear.lxt', 'wb') as f:
    f.write(output)
