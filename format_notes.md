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

The facility index is a variable number of bits from 8 to 32 depending on the total number of facilities in the file. An out-of-range value will cause an error and parsing to be aborted.

The same commands are used as in a normal LXT, but bits [7:4] must be 0.

TODO TAKE A LOOK AT THE DETAILS OF POSITION ADJUSTING


## LXT2

The key change in LXT2 files is that value changes are chunked into blocks of up to either 32 or 64 changes, called a granule. This eliminates the need for a table mapping file positions and time values. Additionally, files are generally intended to be processed in forwards order rather than starting from the end.

Unlike LXT files, it is not possible to start writing out change data until the total count of facilities is known.

The overall structure of an LXT2 file is as follows:

| File contents                     |
| --------------------------------- |
| `hdrid`                           |
| `version`                         |
| `granule_size`                    |
| `numfacs`                         |
| optional expansion bytes          |
| `numfacbytes`                     |
| `longestname`                     |
| `zfacnamesize`                    |
| `zfacname_predec_size`            |
| `zfacgeometrysize`                |
| `timescale`                       |
| gzip compressed facility names    |
| gzip compressed facility geometry |
| block data                        |

### Header fields

`hdrid` is a 16-bit value which must be 0x1380.

`version` is a 16-bit version number. As of this writing, GTKWave supports version numbers less than or equal to 1. The version number specified in the file does not appear to "gate" usage of any newer features or otherwise affect processing of the file in any way. When writing files, `lxt2_write.c` always writes a version number of 1 regardless of what features are used.

`granule_size` is a byte that is supposed to indicate the size of granules in this file. GTKWave only accepts values less than or equal to 64. If this value is specified as 64, granules will contain 64 changes. If this value is any other number, it will be interpreted as granules of size 32.

`numfacs` is a 32-bit value containing the total number of facilities in this file. If it is 0, it indicates the presence of expansion bytes.

`numfacbytes` is a 32-bit value that presumably should contain the total amount of memory needed to store all names _after_ compressed prefixes are all decompressed. However, GTKWave ignores this value. `lxt2_write.c` will consistently overcount this value (in a different way from `lxt_write.c`).

`longestname` is a 32-bit value that must be at least as long as the longest facility name. <span style="color:red">If this value is too small, GTKWave will overflow a heap-allocated buffer with data from the file.</span>

`zfacnamesize` is a 32-bit value containing the size of the gzip compressed facility names.

`zfacname_predec_size` is a 32-bit value containing the size of the facility name data (which is still prefix compressed) to be read from the gzip stream.

`zfacgeometrysize` is a 32-bit value containing the size of the gzip compressed facility geometry.

Unlike in LXT files, LXT2 files need to contain correct compressed sizes on all platforms, as that information is used to seek through the file.

`timescale` is a signed byte containing the timescale. This is in the same format as in the `LT_SECTION_TIMESCALE` section of an LXT file (including the range limitation).

### Header expansion bytes

If the `numfacs` field is zero, the header expansion bytes contain the following:

| Field contents                    |
| --------------------------------- |
| `num_expansion_bytes`             |
| `numfacs` (actual)                |
| `timezero`                        |
| possible future bytes             |

`num_expansion_bytes` is a 32-bit value containing the number of expansion bytes, where the count starts from after this second (actual) `numfacs` field. If this value is less than 8, expansion information is ignored.

`numfacs` is a 32-bit value containing the actual number of facilities.

`timezero` contains a global time offset as in the `LT_SECTION_TIMEZERO` section of LXT files.

### Facility names and geometries

Facility names are encoded in the same way as LXT files (including prefix compression).

Facility geometries are also encoded in the same way as LXT files, except that there are additional flags defined. Flags valid for a LXT file are also valid for LXT2 with the same numeric values. The additional flags presumably allow for specifying properties of symbols defined in HDL, but they do not actually do anything in reality.

Just like in LXT files, arrays (rows > 0) are not properly supported. Unlike in LXT files, there is no way at all to encode an array row in value change data. However, also unlike in LXT files, setting rows to 1 will import the (1-item) array as if it were a scalar value.

As in LXT files, it is possible to store uncompressed data instead of glib compressed data as long as it does not start with glib magic bytes (0x1F 0x8B).

Alias facilities must all be listed at the end after all of the non-alias facilities (or else the non-alias facilities after the first alias facility will not have any data read).

### Blocks

Each block consists of a header followed by compressed data:

| Block contents        |
| --------------------- |
| `uncompressed_size`   |
| `compressed_size`     |
| `start_time`          |
| `end_time`            |
| block data            |

`uncompressed_size` is a 32-bit value containing the size of the block data after decompression.

`compressed_size` is a 32-bit value containing the size of the compressed block data.

`start_time` and `end_time` are 64-bit time values that specify the range of time values contained within this block.

Blocks that have zero `uncompressed_size`, `compressed_size`, or `end_time` are skipped.

There are two formats of blocks, gzip and "striped." The type of blocks is detected by looking for a gzip magic number (0x1F 0x8B).

A gzip block consists of a single gzip stream.

A striped block consists of a sequence of multiple stripe headers followed by what is supposed to be a gzip stream. However, the gzip header and footer will be completely ignored and only the core DEFLATE data will be read.

| <!---->                       |
| ----------------------------- |
| stripe 0 compressed size      |
| stripe 0 uncompressed size    |
| stripe 0 `iter`               |
| stripe 0 gzip data            |
| stripe 1 compressed size      |
| stripe 1 uncompressed size    |
| stripe 1 `iter`               |
| stripe 1 gzip data            |
| ...                           |
| stripe n compressed size      |
| stripe n uncompressed size    |
| stripe n `iter`               |
| stripe n gzip data            |

The purpose of a striped block is supposed to be allowing for a subset of facilities to be read without having to decompress the entire block. In order to properly allow for this, it must be used with `LXT2_RD_GRAN_SECT_TIME_PARTIAL` described below. However, GTKWave will accept "pointless" use of this format.

`iter` is a 32-bit value. When it is 0xffffffff, the stripe will be unconditionally decompressed, and the stripe must be the last one. Otherwise, the stripe will only be decompressed if the `iter` / 2048 group of facilities is marked for processing.

When used properly, facilities will be divided up into groups of up to 2048. The changes for each group will be encoded in a `LXT2_RD_GRAN_SECT_TIME_PARTIAL` section, and each such section will be compressed into one stripe. The `iter` value of this stripe will be set to the first facility index encoded within it. The final section, the shared `LXT2_RD_GRAN_SECT_DICT`, will also be compressed into a stripe, and `iter` will be set to 0xFFFFFFFF. This allows for skipping through blocks of 2048 facilities at a time, decompressing only those containing values of interest.

Note that it is not possible to store raw uncompressed data in this part of the file.

After decompression, **block** data is divided into **sections** prefixed with a type byte. The following type bytes are valid:

| Type                              | Byte  |
| --------------------------------- | ----- |
| LXT2_RD_GRAN_SECT_TIME            | 0     |
| LXT2_RD_GRAN_SECT_DICT            | 1     |
| LXT2_RD_GRAN_SECT_TIME_PARTIAL    | 2     |

`LXT2_RD_GRAN_SECT_TIME` and `LXT2_RD_GRAN_SECT_TIME_PARTIAL` are used to define **granules** while `LXT2_RD_GRAN_SECT_DICT` is used to define a map and dictionary shared by all granules inside a block.

Parsing will stop at the first unrecognized type byte. `LXT2_RD_GRAN_SECT_DICT` must be at the very end of the block.

### `LXT2_RD_GRAN_SECT_DICT`

This section contains a dictionary and map shared by all granules in a block. The format of this section is:

| Section contents              |
| ----------------------------- |
| `LXT2_RD_GRAN_SECT_DICT`      |
| dictionary string 0           |
| ...                           |
| dictionary string n           |
| map entry 0                   |
| ...                           |
| map entry n                   |
| `num_dict_entries`            |
| `dict_size`                   |
| `num_map_entries`             |

Dictionary strings are null-terminated strings. There are `num_dict_entries` entries.

Map entries are either 32-bit or 64-bit bitfields, depending on the `granule_size` of the file. There are `num_map_entries` entries.

`num_dict_entries` is a 32-bit value containing the number of dictionary entries.

`dict_size` is a 32-bit value containing the total size of the dictionary in bytes. If the dictionary does not actually match this size (e.g. if there is junk data after the last string), an error is raised and parsing is aborted.

`num_map_entries` is a 32-bit value containing the number of map entries.

### Granules

Granules can either be a complete granule (encoding every "real" facility) or a partial granule (encoding a subset of up to 2048 facilities).

The format of a complete granule is:

| Granule contents              |
| ----------------------------- |
| `num_time_table_entries`      |
| time table 0                  |
| ...                           |
| time table n                  |
| `fac_map_index_width`         |
| map index 0                   |
| ...                           |
| map index n                   |
| `fac_curpos_width`            |
| value change data 0           |
| ...                           |
| value change data n           |

The format of a partial granule contains two additional fields followed by contents similar to a complete granule:

| Partial granule contents      |
| ----------------------------- |
| `strtfac`                     |
| `sublen`                      |
| `num_time_table_entries`      |
| ... other granule fields      |

`sublen` is a 32-bit value containing the size in bytes of the complete granule data following the partial granule header.

`num_time_table_entries` is an 8-bit value of the number of time table entries following. <span style="color:red">If it is greater than 64, a fixed-sized array in a struct is overflowed and subsequent data is corrupted.</span>

Time table entries are each 64-bit values containing a time value.

In a complete granule, the following sequences (map index, value change data) apply starting at facility index 0 and repeat for the total number of "real" facilities in the file. A "real" facility is supposed to include all facilities except aliases (but, if aliases are incorrectly not stored at the end, this count will be truncated at the first encounter of an alias facility). In a partial granule, the following sequences will only apply to facilities starting from index `strtfac` (32-bit value) and continue for either 2048 entries or until the total number of "real" facilities is reached, whichever is smaller.

`fac_map_index_width` specifies the size in bytes of all subsequent map indices. The valid range is [1 - 4].

For each facility, an index into the map (in `LXT2_RD_GRAN_SECT_DICT`) is stored. The bits that are set in the map bitfield value indicate that this facility has a value change at that particular time. The bit index of the set bits index into the time table to get the actual time values of the changes.

`fac_curpos_width` specifies the size in bytes of subsequent value change entries. The valid range is [1 - 4].

For each facility, value change information is stored. Value change data consists of a sequence of `fac_curpos_width` byte entries. The number of items in this value change sequence is the number of 1 bits set in the map entry for this facility.

TODO test first granule in a block duplicate change elimination

TODO example

### Value change entries

Value change entires either consist of a special shortcut command or else are indices into the dictionary (in `LXT2_RD_GRAN_SECT_DICT`). The following shortcut commands exist:

| Command               | Value |
| --------------------- | ----- |
| LXT2_RD_ENC_0         | 0x0   |
| LXT2_RD_ENC_1         | 0x1   |
| LXT2_RD_ENC_INV       | 0x2   |
| LXT2_RD_ENC_LSH0      | 0x3   |
| LXT2_RD_ENC_LSH1      | 0x4   |
| LXT2_RD_ENC_RSH0      | 0x5   |
| LXT2_RD_ENC_RSH1      | 0x6   |
| LXT2_RD_ENC_ADD1      | 0x7   |
| LXT2_RD_ENC_ADD2      | 0x8   |
| LXT2_RD_ENC_ADD3      | 0x9   |
| LXT2_RD_ENC_ADD4      | 0xa   |
| LXT2_RD_ENC_SUB1      | 0xb   |
| LXT2_RD_ENC_SUB2      | 0xc   |
| LXT2_RD_ENC_SUB3      | 0xd   |
| LXT2_RD_ENC_SUB4      | 0xe   |
| LXT2_RD_ENC_X         | 0xf   |
| LXT2_RD_ENC_Z         | 0x10  |
| LXT2_RD_ENC_BLACKOUT  | 0x11  |

`LXT2_RD_ENC_0/1/X/Z` sets the facility value to all 0/1/X/Z.

`LXT2_RD_ENC_INV` inverts all of the bits of the facility.

`LXT2_RD_ENC_LSH0/1` performs a left shift and shifts in a 0/1 bit.

`LXT2_RD_ENC_RSH0/1` performs a right shift and shifts in a 0/1 bit.

`LXT2_RD_ENC_ADD*` performs an integer addition by the specified constant.

`LXT2_RD_ENC_SUB*` performs an integer subtraction by the specified constant.

`LXT2_RD_ENC_BLACKOUT` seems like it is supposed to mark when a facility is not being dumped, but it does not seem to work properly.

For values >= 0x12, 0x12 is subtracted and the result is used as an index into the dictionary.

Note that, unlike for LXT files, double values are stored in printf `%lg` format (`lxt2_write.c` uses `%.16g`) rather than as binary.


## VZT

VZT files are similar to LXT2 files with the following main changes:

* Within a block, facilities that change in an identical way share their change data rather than storing duplicate information
* Changes are always encoded explicitly. It is never necessary to know the previous value of a facility in order to determine the value at a given time. This change guarantees that it is possible to decode all VZT blocks in parallel (it is possible to encode an LXT2 file such that this is possible, but it is not guaranteed).
* MLT_9 is no longer supported, only MLT_2 and MLT_4 (MLT_9 is theoretically still representable, but GTKWave does not implement it)
* Miscellaneous encoding format changes (variable-size integers, endianness quirks, different compression formats)

The overall structure of a VZT file is almost identical to the LXT2 structure with the following differences:

`hdrid` must be 0x565A ('VZ').

`version` is a 16-bit version number. As of this writing, GTKWave supports version numbers less than or equal to 1. The version number specified in the file does not appear to "gate" usage of any newer features or otherwise affect processing of the file in any way. When writing files, `vzt_write.c` always writes a version number of 1 regardless of what features are used.

`granule_size` is a byte that is supposed to indicate the size of granules in this file. GTKWave only accepts values less than or equal to 32 (granules are always size 32, size 64 is not supported in VZT). However, other than needing to be less than or equal to 32, this value does not affect processing of the file in any way.

Other header fields are identical to LXT2, <span style="color:red">including the buffer overflow that occurs if `longestname` is too small.</span>

### Compression

Multiple compression formats are supported by VZT files, and they are detected by the presence of magic bytes. The supported formats are:

* gzip (0x1F 0x8B)
* LZMA ('z' '7')
* bzip2 (default assumption, but must contain the magic 'B' 'Z')

LZMA does not use a standard container format but instead uses a custom one. This container format allows mixing LZMA-compressed and uncompressed chunks. The container uses the [variable-sized integers](#variable-size-integers) described below, and consists of repeated blocks of:

| <!---->   |
| --------- |
| `dstlen`  |
| `srclen`  |
| data      |

The end of the stream is marked by a `dstlen` of 0 (and `srclen` and data are not read).

If `srclen` is zero, the chunk contains `dstlen` uncompressed bytes. Otherwise, the chunk nominally contains `srclen` bytes which decompresses to `dstlen` bytes (.lzma/LZMA_ALONE format). However, an oversized `dstlen` is ignored (which is different from most other compressed data where a short read is a fatal error).

`dstlen` is also used to compute the size of temporary buffers to use while decompressing (reallocating every time a larger `dstlen` is encountered), and <span style="color:red">if `srclen` ever exceeds this buffer size then a heap overflow occurs.</span>

<span style="color:red">TODO CHECK ME Unlike in the contents of data blocks, if a variable-sized integer happens to exceed 16 bytes, an array on the stack is overflowed.</span>

Unlike LXT2, it is never possible to _directly_ store uncompressed data. One of the supported compression mechanisms must be used. However, uncompressed data can be stored inside the custom LZMA container.

### Facility names and geometries

Facility names and geometries have the same encoding as in LXT2 files. This includes:

* The same numeric values for flags, including the LXT2 HDL attribute flags that are ignored.
* The same lack of complete support for arrays.
* The same requirement that alias facilities be listed at the end.

### Blocks

Blocks contain the same header as in LXT2 files. However, if `start_time` is greater than `end_time`, it indicates that the block contents use run-length-encoding for the value dictionary (the time values are then swapped back into the correct order).3

The compression formats that can be used are gzip, LZMA, and bzip2. "Striped" compression is not supported.

Block _contents_ are **completely different**.

### Variable-size integers

Some fields in block contents are encoded with a variable-size integer format almost identical to ULEB128. However, the high bit of every byte is inverted compared to ULEB128 (i.e. the MSB is **clear** on each byte except the last byte where it is set).

### Block contents

The format of a block is as follows:

| Block contents                |
| ----------------------------- |
| `num_time_ticks`              |
| time table                    |
| `num_sections`                |
| `num_dict_entries`            |
| [padding]                     |
| value dictionary              |
| `num_bitplanes`               |
| [padding]                     |
| vindex table                  |
| `num_str_entries`             |
| string dictionary             |

`num_time_ticks` is a 32-bit modified-ULEB128 value encoding the number of time value entries in the following time table. If this value is 0, no entries are stored and the time table will be treated as if it contains time steps from `start_time` to `end_time` (in the block header) incrementing by 1.

If present, the time table contains 64-bit modified-ULEB128 values. The first value is an absolute time value, and all subsequent values are deltas from the previous time value.

`num_sections` is a 32-bit modified-ULEB128 value encoding the number of 32-bit granules contained in each entry of the value dictionary.

`num_dict_entries` is a 32-bit modified-ULEB128 value encoding the number of entries in the value dictionary.

The value dictionary contains patterns of signal values across the time interval of this block. This section can optionally be RLE-compressed and will be explained further later.

`num_bitplanes` is a byte value encoding 1 less than the number of "bit planes" present in the vindex table. This is used to encode MLT_4 values. Although this can be an arbitrary value, GTKWave does not implement any way for bit planes past 2 to be accessed. **NOTE** that this one field is _not_ a variable-sized integer.

The vindex table contains 32-bit indices into the value dictionary for each bit of each facility in the file. This data is **little-endian**. This will be explained further below.

`num_str_entries` is a 32-bit modified-ULEB128 value encoding the number of entries in the string dictionary.

The string dictionary is a sequence of null-terminated strings. Note that in VZT files this is _only_ used for strings (and not doubles, MLT_9, etc.).

Padding aligns the data to a multiple of 4 bytes.

### Value changes

Each facility in the VZT file is mapped to one or more sequential entries (per bit plane) in the vindex table. The number of entries is equal to the length of the facility (for vectors) or else is 32 for integers/strings or 64 for floating-point values. In other words, all multi-bit signals are broken up and treated as a block of 1-bit signals. The bits are ordered from MSB to LSB first.

If there are multiple bit planes, the bit 0 (the LSB) vindex entries for all facilities is stored, followed by the bit 1 vindex entries, and so on. Note that the number of bit planes is a global (or at least per-block) setting and not a per-signal setting, so using more than 1 bit plane expands the required storage for *all* signals. In practice, this functionality is only used to encode MLT_4 signals.

The vindex table thus contains (total number of signal bits in the file) * (`num_bitplanes`) entries.

The vindex table contains indices into the value dictionary. The value dictionary consists of `num_dict_entries` entries each containing `num_sections` granules (so each vindex skips by `num_sections` 32-bit words in the value dictionary). This data is **little-endian**.

<span style="color:red">An out-of-bounds vindex table entry causes invalid memory to be accessed.</span>

Each entry in the value dictionary encodes bits over time, starting from the LSB of the first 32-bit word up to the MSB of the first 32-bit word, then continuing with the LSB of the second 32-bit word, and so on up to `num_time_ticks` time steps. Each of these time steps then occurs at the time specified in the time table.

If two signals (or two bits inside one vector signal, or even the separate bit plane bits of a MLT_4 signal) have the exact same changes throughout a block, then they can share value dictionary entries. Each vindex table entry would contain the same index into the value dictionary.

Double values are encoded as a 64-bit vector (i.e. a block of 64 contiguous entries in the vindex table) storing IEEE binary64 values.

String values are encoded as a 32-bit vector (i.e. a block of 32 contiguous entries in the vindex table) storing an index into the string dictionary. <span style="color:red">TODO CHECK ME An out-of-bounds index causes invalid memory to be accessed.</span>

TODO GIVE AN EXAMPLE

### RLE compression

The value dictionary can optionally be RLE compressed. When RLE compression is used, contiguous runs of 1 or 0 bits are encoded with a length (32-bit modified-ULEB128 encoding). The decoder starts outputting 1 bits, and the bit being output is toggled after every run (i.e. a run of 1s, then a run of 0s, then a run of 1s, etc.). A run with length 0 can be used invert the future bit to be output (which is only really useful at the beginning in order to start with 0 bits). The RLE decoder consumes runs until the entire dictionary is filled.

TODO GIVE AN EXAMPLE
