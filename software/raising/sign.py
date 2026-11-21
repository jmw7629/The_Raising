"""sign.py: III.26. Lamport one-time signatures over SHA-256.

Private file: {name, seed}; seed is 32 random bytes, hex.
Secrets  x(j,b) = H(f"{seed}|{i}|{j}|{b}")   j 0..255, b 0..1,
i = that name's entries signed so far in this Keep.
Public   P(i)   = H of the 512 H(x) joined in (j,b) order.
sig: 256 pairs [x(j,bit), H(x(j,1-bit))], bit j of the line's hash, high first.
Nothing here opens a Keep; keep.py and desk.py decide which key is expected.
"""
import hashlib
import os


def H(data):
    """Lowercase-hex SHA-256 of UTF-8 bytes (III.52)."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def secret(seed, i, j, b):
    return H(f"{seed}|{i}|{j}|{b}")


def public(seed, i):
    return H("".join(H(secret(seed, i, j, b)) for j in range(256) for b in (0, 1)))


def bits(hexhash):
    """The 256 bits of a hash, high first."""
    n = int(hexhash, 16)
    return [(n >> (255 - j)) & 1 for j in range(256)]


def sign(seed, i, hexhash):
    out = []
    for j, bit in enumerate(bits(hexhash)):
        out.append([secret(seed, i, j, bit), H(secret(seed, i, j, 1 - bit))])
    return out


def wellformed(sig):
    if not isinstance(sig, list) or len(sig) != 256:
        return False
    for pair in sig:
        if not isinstance(pair, list) or len(pair) != 2:
            return False
        for s in pair:
            if not isinstance(s, str) or len(s) != 64:
                return False
            try:
                int(s, 16)
            except ValueError:
                return False
    return True


def recover(sig, hexhash):
    """Hash each revealed x, place both by bit, rebuild P(i). None if malformed."""
    if not wellformed(sig):
        return None
    parts = []
    for j, bit in enumerate(bits(hexhash)):
        x, other = sig[j]
        hx = H(x)
        parts.append(hx + other if bit == 0 else other + hx)
    return H("".join(parts))


def new_key(name):
    return {"name": name, "seed": os.urandom(32).hex()}
