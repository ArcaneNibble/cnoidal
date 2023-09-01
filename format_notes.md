# An _actual_ LXT/LXT2/VZT format documentation

The manual for GTKWave has an incomplete documentation of the LXT format in Appendix D and no documentation of LXT2 or VZT. This document will attempt to provide full documentation of all three formats as implemented in the current GTKWave source code as of TODO DATE (including implementation bugs and quirks).


## LXT

The design goals for this format _appear_ to have been:
* a binary format
* similar to VCD, but supporting more data types
* where subsets of signals (facilities) can be read without having to read the entire file, except for the fact that this is no longer possible when compression is used

### Overall structure

Unless otherwise stated, all values are **big-endian**. Out-of-range offsets and undersized sections are, in general, not checked and cause invalid data to be read.

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

#### `LT_SECTION_ZFACNAME_SIZE`

If this section is present and nonzero, it indicates that data in the `LT_SECTION_FACNAME` section is compressed with gzip. The data that is compressed includes everything **except** the first 8 bytes (consisting of `number_of_facilities` and `facility_name_total_memory`):

| Section contents              |
| ----------------------------- |
| `number_of_facilities`        |
| `facility_name_total_memory`  |
| gzip compressed data          |

The size of the gzip-compressed data is stored as the value of this section (TODO CHECK THE FOLLOWING), although having an accurate value is only important on Windows.

The number of bytes that will be decompressed is stored as the value of the `LT_SECTION_ZFACNAME_PREDEC_SIZE` section. (TODO CHECK THE FOLLOWING). If there are fewer bytes in the compressed stream than this, an error occurs and parsing of the entire file is aborted. If there are more bytes in the compressed stream than this, the remaining bytes are ignored.

#### `LT_SECTION_ZFACNAME_GEOMETRY_SIZE`

If this section is present and nonzero, it indicates that data in the `LT_SECTION_FACNAME_GEOMETRY` section is compressed with gzip. Everything is compressed:

| Section contents              |
| ----------------------------- |
| gzip compressed data          |

The size of the gzip-compressed data is stored as the value of this section (TODO CHECK THE FOLLOWING), although having an accurate value is only important on Windows.

The number of bytes that will be decompressed is 16 * the total number of facilities (found in the  `LT_SECTION_FACNAME` section). (TODO CHECK THE FOLLOWING). If there are fewer bytes in the compressed stream than this, an error occurs and parsing of the entire file is aborted. If there are more bytes in the compressed stream than this, the remaining bytes are ignored.

#### `LT_SECTION_ZSYNC_SIZE`

This section is only read if `LT_SECTION_SYNC_TABLE` is present and nonzero. If both that section and this section are present and nonzero, it indicates that data in the `LT_SECTION_SYNC_TABLE` section is compressed with gzip. Everything is compressed:

| Section contents              |
| ----------------------------- |
| gzip compressed data          |

The size of the gzip-compressed data is stored as the value of this section (TODO CHECK THE FOLLOWING), although having an accurate value is only important on Windows.

The number of bytes that will be decompressed is 4 * the total number of facilities (found in the  `LT_SECTION_FACNAME` section). (TODO CHECK THE FOLLOWING). If there are fewer bytes in the compressed stream than this, an error occurs and parsing of the entire file is aborted. If there are more bytes in the compressed stream than this, the remaining bytes are ignored.

#### `LT_SECTION_ZTIME_TABLE_SIZE`

If this section is present and nonzero, it indicates that data in the `LT_SECTION_TIME_TABLE`/`LT_SECTION_TIME_TABLE64` section is compressed with gzip. The data that is compressed includes everything **except** the first 4 bytes (consisting of `number_of_entries`):

| Section contents              |
| ----------------------------- |
| `number_of_entries`           |
| gzip compressed data          |

This section (`LT_SECTION_ZTIME_TABLE_SIZE`) is used regardless of whether the time table is 32-bit or 64-bit.

The size of the gzip-compressed data is stored as the value of this section (TODO CHECK THE FOLLOWING), although having an accurate value is only important on Windows.

The number of bytes that will be decompressed depends on whether the file contains a `LT_SECTION_TIME_TABLE` or `LT_SECTION_TIME_TABLE64` section (a file that contains both will cause an error and cause parsing to be aborted). In case of 32-bit time, the amount of data is 4 + 4 + 4 * `number_of_entries` bytes. In case of 64-bit time, the amount of data is 8 + 8 + 12 * `number_of_entries` bytes. (TODO CHECK THE FOLLOWING). If there are fewer bytes in the compressed stream than this, an error occurs and parsing of the entire file is aborted. If there are more bytes in the compressed stream than this, the remaining bytes are ignored.

#### `LT_SECTION_ZCHG_SIZE`

