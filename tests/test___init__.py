# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import functools
import itertools

import pytest

import crc32c


EMPTY = b""
EMPTY_CRC = 0x00000000

# From: https://tools.ietf.org/html/rfc3720#appendix-B.4
#
#   32 bytes of zeroes:
#
#     Byte:        0  1  2  3
#
#        0:       00 00 00 00
#      ...
#       28:       00 00 00 00
#
#      CRC:       aa 36 91 8a

ALL_ZEROS = b"\x00" * 32
ALL_ZEROS_CRC = 0x8A9136AA

#   32 bytes of ones:
#
#     Byte:        0  1  2  3
#
#        0:       ff ff ff ff
#      ...
#       28:       ff ff ff ff
#
#      CRC:       43 ab a8 62

ALL_ONES = b"\xff" * 32
ALL_ONES_CRC = 0x62A8AB43

#
#   32 bytes of incrementing 00..1f:
#
#     Byte:        0  1  2  3
#
#        0:       00 01 02 03
#      ...
#       28:       1c 1d 1e 1f
#
#      CRC:       4e 79 dd 46

INCREMENTING = bytes(range(32))
INCREMENTING_CRC = 0x46DD794E

#
#   32 bytes of decrementing 1f..00:
#
#     Byte:        0  1  2  3
#
#        0:       1f 1e 1d 1c
#      ...
#       28:       03 02 01 00
#
#      CRC:       5c db 3f 11

DECREMENTING = bytes(reversed(range(32)))
DECREMENTING_CRC = 0x113FDB5C

#
#    An iSCSI - SCSI Read (10) Command PDU
#
#    Byte:        0  1  2  3
#
#       0:       01 c0 00 00
#       4:       00 00 00 00
#       8:       00 00 00 00
#      12:       00 00 00 00
#      16:       14 00 00 00
#      20:       00 00 04 00
#      24:       00 00 00 14
#      28:       00 00 00 18
#      32:       28 00 00 00
#      36:       00 00 00 00
#      40:       02 00 00 00
#      44:       00 00 00 00
#
#     CRC:       56 3a 96 d9

ISCSI_SCSI_READ_10_COMMAND_PDU = [
    0x01,
    0xC0,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x14,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x04,
    0x00,
    0x00,
    0x00,
    0x00,
    0x14,
    0x00,
    0x00,
    0x00,
    0x18,
    0x28,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x02,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
]
ISCSI_LENGTH = len(ISCSI_SCSI_READ_10_COMMAND_PDU)
ISCSI_BYTES = bytes(ISCSI_SCSI_READ_10_COMMAND_PDU)
ISCSI_CRC = 0xD9963A56


_EXPECTED = [
    (EMPTY, EMPTY_CRC),
    (ALL_ZEROS, ALL_ZEROS_CRC),
    (ALL_ONES, ALL_ONES_CRC),
    (INCREMENTING, INCREMENTING_CRC),
    (DECREMENTING, DECREMENTING_CRC),
    (ISCSI_SCSI_READ_10_COMMAND_PDU, ISCSI_CRC),
    (ISCSI_BYTES, ISCSI_CRC),
]


def test_extend_w_empty_chunk():
    crc = 123
    assert crc32c.extend(crc, b"") == crc


def test_extend_w_multiple_chunks():
    crc = 0

    for index in itertools.islice(range(ISCSI_LENGTH), 0, None, 7):
        chunk = ISCSI_SCSI_READ_10_COMMAND_PDU[index : index + 7]
        crc = crc32c.extend(crc, chunk)

    assert crc == ISCSI_CRC


def test_extend_w_reduce():
    chunks = (
        ISCSI_BYTES[index : index + 3]
        for index in itertools.islice(range(ISCSI_LENGTH), 0, None, 3)
    )
    assert functools.reduce(crc32c.extend, chunks, 0) == ISCSI_CRC


@pytest.mark.parametrize("chunk, expected", _EXPECTED)
def test_value(chunk, expected):
    assert crc32c.value(chunk) == expected


class TestChecksum(object):
    @staticmethod
    def test_ctor_defaults():
        helper = crc32c.Checksum()
        assert helper._crc == 0

    @staticmethod
    def test_ctor_explicit():
        chunk = b"DEADBEEF"
        helper = crc32c.Checksum(chunk)
        assert helper._crc == crc32c.value(chunk)

    @staticmethod
    def test_update():
        chunk = b"DEADBEEF"
        helper = crc32c.Checksum()
        helper.update(chunk)
        assert helper._crc == crc32c.value(chunk)

    @staticmethod
    def test_update_w_multiple_chunks():
        helper = crc32c.Checksum()

        for index in itertools.islice(range(ISCSI_LENGTH), 0, None, 7):
            chunk = ISCSI_SCSI_READ_10_COMMAND_PDU[index : index + 7]
            helper.update(chunk)

        assert helper._crc == ISCSI_CRC

    @staticmethod
    def test_digest_zero():
        helper = crc32c.Checksum()
        assert helper.digest() == b"\x00" * 4

    @staticmethod
    def test_digest_nonzero():
        helper = crc32c.Checksum()
        helper._crc = 0x01020304
        assert helper.digest() == b"\x01\x02\x03\x04"

    @staticmethod
    def test_hexdigest_zero():
        helper = crc32c.Checksum()
        assert helper.hexdigest() == b"00" * 4

    @staticmethod
    def test_hexdigest_nonzero():
        helper = crc32c.Checksum()
        helper._crc = 0x091A3B2C
        assert helper.hexdigest() == b"091a3b2c"

    @staticmethod
    def test_copy():
        chunk = b"DEADBEEF"
        helper = crc32c.Checksum(chunk)
        clone = helper.copy()
        before = helper._crc
        helper.update(b"FACEDACE")
        assert clone._crc == before
