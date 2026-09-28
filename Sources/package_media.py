"""Anki v3 MediaEntries wire format; preserve original entries verbatim."""
import hashlib
import zstandard


def varint(value):
    data = bytearray()
    while value > 127:
        data.append((value & 127) | 128)
        value >>= 7
    data.append(value)
    return bytes(data)


def field(tag, value):
    return varint(tag) + varint(len(value)) + value


def entries(raw):
    offset = 0
    result = []
    while offset < len(raw):
        if raw[offset] != 10:
            raise ValueError('Unsupported media map')
        offset += 1
        size, shift = 0, 0
        while True:
            byte = raw[offset]
            offset += 1
            size |= (byte & 127) << shift
            if byte < 128:
                break
            shift += 7
            if shift > 63:
                raise ValueError('Invalid media map')
        end = offset + size
        if end > len(raw):
            raise ValueError('Truncated media map')
        result.append(raw[offset:end])
        offset = end
    return result


def append_media(raw, name, data):
    entry = field(10, name.encode()) + varint(16) + varint(len(data)) + field(26, hashlib.sha1(data).digest())
    return raw + field(10, entry)


def decode(data):
    return zstandard.ZstdDecompressor().decompress(data)


def encode(data):
    return zstandard.ZstdCompressor(level=3).compress(data)
