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

TODO TEST IF GZIP DATA ISN'T ACTUALLY GZIP

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

This section is always compressed. TODO TODO TODO

### Linear LXT

TODO TODO TODO

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

This section stores a 64-bit time offset for all timestamps in this file (i.e. time 0 in the file will be displayed to a user as time `global_time_offset` (taking into account the timescale)).

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

