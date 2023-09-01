# An _actual_ LXT/LXT2/VZT format documentation

The manual for GTKWave has an incomplete documentation of the LXT format in Appendix D and no documentation of LXT2 or VZT. This document will attempt to provide full documentation of all three formats as implemented in the current GTKWave source code as of TODO DATE (including implementation bugs and quirks).


## LXT

The design goals for this format _appear_ to have been:
* a binary format
* similar to VCD, but supporting more data types
* where subsets of signals (facilities) can be read without having to read the entire file, except for the fact that this is no longer possible when compression is used

### Overall structure

Unless otherwise stated, all values are **big-endian**. <span style="color:red">Out-of-range offsets and undersized sections are, in general, not checked and cause invalid data to be read.</span>

An LXT is structured like the following:

| File contents     |
| ----------------- |
| `hdrid`           |
| `version`         |
| body              |
| section pointer   |
| section pointer   |
| ...               |
| section pointer   |
| `trlid`           |

`hdrid` is a 16-bit value which must be 0x0138

`version` is a 16-bit version number. As of this writing, GTKWave supports version numbers less than or equal to 4. The version number specified in the file does not appear to "gate" usage of any newer features or otherwise affect processing of the file in any way. When writing files, `lxt_write.c` always writes a version number of 4 regardless of what features are used, and despite code comments referencing a version 5 and 6.

`trlid` must be the byte 0xB4.

### Section pointers

Sections are processed in sequence starting from the end of the file and moving backwards. Tags can be in any order and can be duplicated. In case of duplicates, the last instance encountered (i.e. furthest from the end of the file before the `LT_SECTION_END` tag is encountered, or, in other words, the closest to the `LT_SECTION_END` tag) is used.

With the exception of `LT_SECTION_END`, each section pointer consists of a 4-byte value and a 1-byte type tag:

| One section pointer |
| ------------------- |
| `value`             |
| `tag`               |

`LT_SECTION_END` consists of only the tag byte and is not preceded by a 4-byte value. Processing of sections stops once the first (i.e. closest to the end of the file) `LT_SECTION_END` is encountered.

| End section tag               |
| ----------------------------- |
| `tag` = LT_SECTION_END (0x00) |

`value` was originally supposed to be a 4-byte offset from the beginning of the file. TODO TEST 2GB/4GB limit However, certain tags instead use this value to store a 4-byte size instead. This will be explained in more detail below.

The following `tag` values are currently supported:
| Section type                      | Tag byte value    |
| --------------------------------- | ----------------- |
| LT_SECTION_END                    | 0x00              |
| LT_SECTION_CHG                    | 0x01              |
| LT_SECTION_SYNC_TABLE             | 0x02              |
| LT_SECTION_FACNAME                | 0x03              |
| LT_SECTION_FACNAME_GEOMETRY       | 0x04              |
| LT_SECTION_TIMESCALE              | 0x05              |
| LT_SECTION_TIME_TABLE             | 0x06              |
| LT_SECTION_INITIAL_VALUE          | 0x07              |
| LT_SECTION_DOUBLE_TEST            | 0x08              |
| LT_SECTION_TIME_TABLE64           | 0x09              |
| LT_SECTION_ZFACNAME_PREDEC_SIZE   | 0x0A              |
| LT_SECTION_ZFACNAME_SIZE          | 0x0B              |
| LT_SECTION_ZFACNAME_GEOMETRY_SIZE | 0x0C              |
| LT_SECTION_ZSYNC_SIZE             | 0x0D              |
| LT_SECTION_ZTIME_TABLE_SIZE       | 0x0E              |
| LT_SECTION_ZCHG_PREDEC_SIZE       | 0x0F              |
| LT_SECTION_ZCHG_SIZE              | 0x10              |
| LT_SECTION_ZDICTIONARY            | 0x11              |
| LT_SECTION_ZDICTIONARY_SIZE       | 0x12              |
| LT_SECTION_EXCLUDE_TABLE          | 0x13              |
| LT_SECTION_TIMEZERO               | 0x14              |

### Compression

The presence of certain section tags indicates that data in another section is compressed.

In cases where data is supposed to be compressed with gzip, it is possible to store uncompressed data instead as long as the uncompressed data does not start with a gzip header (0x1F 0x8B). There is usually no point in doing this, but this can be used to store uncompressed data in the `LT_SECTION_ZDICTIONARY` section.

(TODO CHECK THE FOLLOWING) The size of the compressed data in bytes should be specified as the value of a `*_SIZE` section, although having an accurate value is only important on Windows. On non-Windows, the value merely has to be nonzero.

(TODO CHECK THE FOLLOWING). If the compressed stream contains fewer bytes than expected (either specified by a `*_PREDEC_SIZE` tag or otherwise computed), an error occurs and parsing of the entire file is aborted. If there are more bytes in the compressed stream than expected, the remaining bytes are ignored.

#### `LT_SECTION_ZFACNAME_SIZE`

If this section is present and nonzero, it indicates that data in the `LT_SECTION_FACNAME` section is compressed with gzip. The data that is compressed includes everything **except** the first 8 bytes (consisting of `number_of_facilities` and `facility_name_total_memory`):

| Section contents              |
| ----------------------------- |
| `number_of_facilities`        |
| `facility_name_total_memory`  |
| gzip compressed data          |

The size of the gzip-compressed data is stored as the value of this section.

The number of bytes that will be decompressed is stored as the value of the `LT_SECTION_ZFACNAME_PREDEC_SIZE` section.

#### `LT_SECTION_ZFACNAME_GEOMETRY_SIZE`

If this section is present and nonzero, it indicates that data in the `LT_SECTION_FACNAME_GEOMETRY` section is compressed with gzip. Everything is compressed:

| Section contents              |
| ----------------------------- |
| gzip compressed data          |

The size of the gzip-compressed data is stored as the value of this section.

The number of bytes that will be decompressed is 16 * the total number of facilities (found in the  `LT_SECTION_FACNAME` section).

#### `LT_SECTION_ZSYNC_SIZE`

This section is only read if `LT_SECTION_SYNC_TABLE` is present and nonzero. If both that section and this section are present and nonzero, it indicates that data in the `LT_SECTION_SYNC_TABLE` section is compressed with gzip. Everything is compressed:

| Section contents              |
| ----------------------------- |
| gzip compressed data          |

The size of the gzip-compressed data is stored as the value of this section.

The number of bytes that will be decompressed is 4 * the total number of facilities (found in the  `LT_SECTION_FACNAME` section).

#### `LT_SECTION_ZTIME_TABLE_SIZE`

If this section is present and nonzero, it indicates that data in the `LT_SECTION_TIME_TABLE`/`LT_SECTION_TIME_TABLE64` section is compressed with gzip. The data that is compressed includes everything **except** the first 4 bytes (consisting of `number_of_entries`):

| Section contents              |
| ----------------------------- |
| `number_of_entries`           |
| gzip compressed data          |

This section (`LT_SECTION_ZTIME_TABLE_SIZE`) is used regardless of whether the time table is 32-bit or 64-bit.

The size of the gzip-compressed data is stored as the value of this section.

The number of bytes that will be decompressed depends on whether the file contains a `LT_SECTION_TIME_TABLE` or `LT_SECTION_TIME_TABLE64` section (a file that contains both will cause an error and cause parsing to be aborted). In case of 32-bit time, the amount of data is 4 + 4 + 4 * `number_of_entries` bytes. In case of 64-bit time, the amount of data is 8 + 8 + 12 * `number_of_entries` bytes.

#### `LT_SECTION_ZCHG_SIZE`

If this section is present and nonzero, it indicates that data in the `LT_SECTION_CHG` section is compressed with either gzip or bzip2. bzip2 is detected by looking for the magic bytes 'BZ' at the beginning of the `LT_SECTION_CHG` section. If these magic bytes are not present, the data is assumed to be gzip. Everything is compressed:

| Section contents              |
| ----------------------------- |
| gzip/bzip2 compressed data    |

TODO WTF IS LINEAR LXT

After decompression, the change data is treated **as if** it was placed at file offset 4.

The size of the compressed data is stored as the value of this section.

The number of bytes that will be decompressed is stored as the value of the `LT_SECTION_ZCHG_PREDEC_SIZE` section.

#### `LT_SECTION_ZDICTIONARY`

This section is always compressed with gzip and will be explained later in this document.

### Sections

If a section does have documentation in the GTKWave manual, this document will only focus on information that is not explicitly documented.

#### `LT_SECTION_TIMESCALE`

| Section contents  |
| ----------------- |
| `timescale`       |

This section contains a single (signed) byte representing the timescale of the file (i.e. a time value of 1 in the file represents $10^{timescale}$ seconds).

Contrary to the manual, the valid range is not [-128 - 127]. Values outside of the range [-21 - 2] (i.e. 1 zeptosecond to 100 seconds) are treated as 1 nanosecond. In addition, if this section is not present, the default timescale is 1 nanosecond.

#### `LT_SECTION_INITIAL_VALUE`

| Section contents  |
| ----------------- |
| `initial_value`   |

This section contains a single byte representing the initial value of all signals. The intended range of valid bytes is [0 - 8] representing `01ZXHUWL-` in order. A byte value outside of this range is also interpreted as `X`. If this section does not exist, the initial value is `X`.

#### `LT_SECTION_DOUBLE_TEST`

| Section contents  |
| ----------------- |
| `pi_constant`     |

This section stores the value 3.14159 as an 8-byte double-precision floating-point value. The intention is for the value to be written in the native byte ordering of the writing software, and for reading software to swap byte ordering if necessary. Byte ordering does not need to be fully big or little endian (i.e. mixed-endian is supported), and GTKWave implements arbitrary byte permuting.

On most modern platforms, this value is an IEEE 754 binary64. The manual does not specify what should happen on platforms that do not natively use such a representation for floating-point numbers. The behavior also appears to be undefined if an incorrect value is stored in this section. The behavior also appears to be undefined if floating-point values are used in the rest of the file but this section is not present. TODO TEST MORE

#### `LT_SECTION_TIMEZERO`

| Section contents      |
| --------------------- |
| `global_time_offset`  |

This section stores a (signed) 64-bit time offset that will be added to all timestamps in this file. A similar rendering effect can be achieved by changing `first_cycle` in the `LT_SECTION_TIME_TABLE`, but the semantic meaning of this section is different. The value in this section corresponds to `$timezero` in VCD files, and negative values always work.

#### `LT_SECTION_EXCLUDE_TABLE`

| Section contents      |
| --------------------- |
| `num_blackouts`       |
| `start[0]`            |
| `end[0]`              |
| `start[1]`            |
| `end[1]`              |
| ...                   |
| `start[n]`            |
| `end[n]`              |

This section stores a list of time intervals that are marked as excluded or blacked-out (e.g. by something like `$dumpoff`). Value changes inside an excluded interval will still be rendered.

`num_blackouts` is a 32-bit count of entries that follow.

`start` and `end` are 64-bit time values.

#### `LT_SECTION_TIME_TABLE` / `LT_SECTION_TIME_TABLE64`

| Section contents              |
| ----------------------------- |
| `number_of_entries`           |
| `first_cycle`                 |
| `last_cycle`                  |
| `position_delta[0]`           |
| `position_delta[1]`           |
| ...                           |
| `position_delta[n]`           |
| `time_delta[0]`               |
| `time_delta[1]`               |
| ...                           |
| `time_delta[n]`               |

This section maps between file positions and time values.

`number_of_entries` is a 32-bit count of the number of delta entries that follow.

`first_cycle` and `last_cycle` are either 32-bit or 64-bit depending on the section type. These store the minimum and maximum time values represented in this file. For 32-bit values, these are interpreted as unsigned. For 64-bit values, they are interpreted as signed, but it is not possible to place cursors in the GUI at negative times.

`position_delta` entries are 32-bit in both cases.

`time_delta` entries are 32-bit or 64-bit depending on the section type.

Contrary to the text in the manual, delta values may be zero as well as positive. This is needed in order to represent values at time 0 and is visible in the example in the manual written immediately after said text requiring values to be positive.

Note further that the order of the position and time information is reversed in the example written in the manual.

#### `LT_SECTION_FACNAME`

| Section contents              |
| ----------------------------- |
| `number_of_facilities`        |
| `facility_name_total_memory`  |
| `prefix_bytes[0]`             |
| `name[0][len]`                |
| `prefix_bytes[1]`             |
| `name[1][len]`                |
| ...                           |
| `prefix_bytes[n]`             |
| `name[n][len]`                |

This section stores the number of signals (facilities) and their names. Names are compressed by reusing prefixes.

`number_of_facilities` is a 32-bit value. This value will also control the amount of data read from many other sections of the file.

`facility_name_total_memory` is a 32-bit value that must be at least as large as the total amount of memory needed to store all names _after_ compressed prefixes are all decompressed. This value may be larger than required, and `lxt_write.c` will consistently overcount this value when bracket stripping is enabled. <span style="color:red">If this value is too small, GTKWave will overflow a heap-allocated buffer with data from the file.</span>

Each name consists of a 16-bit `prefix_bytes` followed by a null-terminated string. To decode each name, copy `prefix_bytes` bytes from the previous name and then append the current name. If `prefix_bytes` exceeds the length of the previous name, the current name will be the same as the previous name (because a null terminator byte will be prematurely copied and inserted). If `prefix_bytes` is nonzero for the first name in the list, uninitialized memory will be read.

It is unspecified what happens if duplicate names are found, but GTKWave will display only one of them.

Names must be UTF-8. Invalid UTF-8 will cause GTKWave to segfault (at least on macOS).

#### `LT_SECTION_FACNAME_GEOMETRY`

| Section contents              |
| ----------------------------- |
| `rows[0]` / `alias_idx[0]`    |
| `msb[0]`                      |
| `lsb[0]`                      |
| `flags[0]`                    |
| `rows[1]` / `alias_idx[1]`    |
| `msb[1]`                      |
| `lsb[1]`                      |
| `flags[1]`                    |
| ...                           |
| `rows[n]` / `alias_idx[n]`    |
| `msb[n]`                      |
| `lsb[n]`                      |
| `flags[n]`                    |

All values are 32 bits.

`rows` is used when `flags` does not contain the flag `LT_SYM_F_ALIAS`. It is supposed to be used to indicate the size of an array, but setting it to anything other than 0 breaks the importing of the trace into GTKWave (`/* sorry, arrays not supported */`).

`alias_idx` is used when `flags` does contain the flag `LT_SYM_F_ALIAS`. It contains an index to another facility to which this facility is an alias to. If there is an alias cycle, GTKWave will infinite loop forever while parsing. <span style="color:red">If the alias is out-of-bounds, invalid memory will be accessed.</span>

`msb` and `lsb` are signed integers containing the MSB and LSB indices of a vector. The bit width of this facility is 1 greater than the difference between these values. If both of these are -1, GTKWave will not append any brackets to the end of the name.

`flags` modify the interpretation of the facility and some of the other fields. The following flags are defined:

| Flag                  | Val   |
| --------------------- | ----- |
| `LT_SYM_F_BITS`       | 0     |
| `LT_SYM_F_INTEGER`    | 1<<0  |
| `LT_SYM_F_DOUBLE`     | 1<<1  |
| `LT_SYM_F_STRING`     | 1<<2  |
| `LT_SYM_F_ALIAS`      | 1<<3  |

`LT_SYM_F_BITS` is not an actual flag at all and is the default interpretation of the facility.

`LT_SYM_F_INTEGER` forces `msb` to 31 and `lsb` to 0 and forces brackets to not display in the name.

`LT_SYM_F_DOUBLE` indicates that this facility contains floating-point values. `msb` and `lsb` will be ignored.

`LT_SYM_F_STRING` indicates that this facility contains string values. `msb` and `lsb` will be ignored.

`LT_SYM_F_ALIAS` indicates that this facility is an alias for another facility. Other flags will be ignored.

Flags seem like they are supposed to be mutually-exclusive, but GTKWave does not explicitly forbid usage where they are not.

#### `LT_SECTION_SYNC_TABLE`

| Section contents              |
| ----------------------------- |
| `offset[0]`                   |
| `offset[1]`                   |
| ...                           |
| `offset[n]`                   |

If this section is present, it contains offsets to the final (latest in time) value change for each facility.

If this section is not present, it indicates the LXT file is encoded with linear encoding.

#### `LT_SECTION_ZDICTIONARY`

| Section contents              |
| ----------------------------- |
| `dict_num_entries`            |
| `dict_string_mem_required`    |
| `dict_16_offset`              |
| `dict_24_offset`              |
| `dict_32_offset`              |
| `dict_width`                  |
| gzip compressed entries       |

A dictionary can be used to compress wide facilities that contain frequent repeated values. Instead of encoding the value every time, an index into the dictionary is encoded instead.

All of the listed header fields are 32 bits.

Dictionary entries are compressed with gzip. The size of the gzip-compressed data is stored as the value of the `LT_SECTION_ZDICTIONARY_SIZE` section. The number of bytes that will be decompressed is stored in `dict_string_mem_required`.

`dict_num_entries` contains the number of entries in the dictionary.

Dictionary indices within change data are variable size. `dict_16_offset` indicates the file offset starting from which indices become 16 bits wide. Before this offset (or if this offset is 0), indices are 8 bits wide. Likewise, `dict_24_offset` indicates the file offset starting from which indices become 24 bits wide. Before this offset (or if this offset is 0), indices are 8 or 16 bits wide. `dict_32_offset` indicates the file offset starting from which indices become 32 bits wide. Before this offset (or if this offset is 0), indices are 8/16/24 bits wide.

Facilities will only index into the dictionary if they are greater than `dict_width` bits wide. Smaller facilities will contain inline MVL2 data as normal.

The compressed data consists of a sequence of null-terminated ASCII MVL9 strings (i.e. consisting of the characters `01ZXHUWL-`). 

When a dictionary entry is referenced, it is prepended (i.e. on the left/MSB) with a leading 1 bit. It is then padded to the width of the facility with 0 bits. <span style="color:red">If this exceeds the size of the facility (i.e. the length of the string in the dictionary is greater than the facility width minus 1) then memory is overwritten with '0' characters until a segfault occurs.</span> Out-of-range indices cause a nonfatal error and result in a value consisting of all 0 bits.

#### `LT_SECTION_CHG`

This is the main section of the file and contains value change data.

However, if the LXT file is not using compression for this section, the section does not actually need to formally exist. Data will instead be processed by following the back pointers in `LT_SECTION_SYNC_TABLE` (for a normal LXT) or blindly starting from file offset 4 (for a linear LXT). This also implies that change data in an uncompressed normal LXT file need not be contiguous and can be freely dispersed throughout the file.

In a compressed LXT, this section must exist, and compressed data will be read starting from this section's offset.

There are two possible encodings for this section of the file, "normal" and "linear."

##### Normal LXT

This is the format as documented in the GTKWave manual. Each change consists of a command byte, delta offset back pointer, optional array row, and optional additional data.

Bits [7:6] of the command byte must be 0.

As described in the [`LT_SECTION_ZDICTIONARY`](#lt_section_zdictionary-1) section, MVL_2 commands can  optionally reference a dictionary. However, this does **not** work for doubles or strings.

MVL_9 values that are out of range are treated as X.

##### Linear LXT

This is an alternative format. When this format is used, it is not possible to read the information for a single facility without scanning through the entire change data.

In a linear LXT, the size of the change data must be encoded as the value of the `LT_SECTION_ZCHG_PREDEC_SIZE` section.

Change data consists of a facility index, command byte, optional array row, and optional additional data.

The facility index is a variable number of bits from 8 to 32 depending on the total number of facilities in the file.

The same commands are used as in a normal LXT, but bits [7:4] must be 0.