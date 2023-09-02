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
output += struct.pack(">IIII", 0, 0xffffffff, 0xffffffff, 0)

#####

# LT_SECTION_CHG
def put_cmd(cmd_b, off_next):
    global output
    off_this = len(output)
    off_delta = off_this - off_next - 2
    if off_delta <= 0xFF:
        output += struct.pack(">BB", cmd_b, off_delta)
    elif off_delta <= 0xFFFF:
        output += struct.pack(">BH", cmd_b | 0x10, off_delta)
    elif off_delta <= 0xFFFFFF:
        output += struct.pack(">B3s", cmd_b | 0x20, off_delta.to_bytes(3))
    elif off_delta <= 0xFFFFFFFF:
        output += struct.pack(">BI", cmd_b | 0x30, off_delta)
    else:
        assert False

offs = []
offs.append(len(output))
put_cmd(0x04, 0)            # 1

offs.append(len(output))
put_cmd(0x03, offs[-2])     # 0

offs.append(len(output))
put_cmd(0x04, offs[-2])     # 1

offs.append(len(output))
put_cmd(0x0c, offs[-2])     # clk
output += b'\x02'

offs.append(len(output))
put_cmd(0x05, offs[-2])     # Z

#####

# LT_SECTION_TIME_TABLE
time_table_off = len(output)
output += struct.pack(">I", 5)
output += struct.pack(">II", 0, 100)

# pos delta
output += struct.pack(">I", offs[0])
output += struct.pack(">I", offs[1] - offs[0])
output += struct.pack(">I", offs[2] - offs[1])
output += struct.pack(">I", offs[3] - offs[2])
output += struct.pack(">I", offs[4] - offs[3])

# time delta
output += struct.pack(">I", 5)
output += struct.pack(">I", 10)
output += struct.pack(">I", 7)
output += struct.pack(">I", 3)
output += struct.pack(">I", 0)

#####

# LT_SECTION_SYNC_TABLE
sync_table_off = len(output)
output += struct.pack(">I", offs[-1])

#####

output += b'\x00'                                       # LT_SECTION_END
output += struct.pack(">IB", facname_off, 3)            # LT_SECTION_FACNAME
output += struct.pack(">IB", facname_geom_off, 4)       # LT_SECTION_FACNAME_GEOMETRY
output += struct.pack(">IB", time_table_off, 6)         # LT_SECTION_TIME_TABLE
output += struct.pack(">IB", sync_table_off, 2)         # LT_SECTION_SYNC_TABLE

output += b'\xB4'   # trlid

with open('clock.lxt', 'wb') as f:
    f.write(output)
