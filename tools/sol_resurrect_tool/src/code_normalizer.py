import re


def normalize_primitive_type_aliases(code: str) -> str:
    """Repair polluted Solidity primitive type names such as `_address`.

    These aliases are not user-defined types. They are artifacts from partial
    source extraction or over-eager identifier sanitization, so they should be
    normalized before symbol repair tries to synthesize missing definitions.
    """
    aliases = {
        "_address": "address",
        "_bool": "bool",
        "_string": "string",
        "_bytes": "bytes",
        "_byte": "bytes1",
        "_uint": "uint256",
        "_int": "int256",
    }
    for bits in range(8, 257, 8):
        aliases[f"_uint{bits}"] = f"uint{bits}"
        aliases[f"_int{bits}"] = f"int{bits}"
        aliases[f"_bytes{bits // 8}"] = f"bytes{bits // 8}"

    for bad, good in sorted(aliases.items(), key=lambda item: len(item[0]), reverse=True):
        code = re.sub(rf"\b{re.escape(bad)}\b", good, code)
    return code
