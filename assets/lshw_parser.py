"""
LSHW Parser Utility
Ported from the FastAPI app - same logic, just cleaner organization

This module parses lshw (Linux Hardware Lister) JSON output to extract:
- Device serial numbers
- CPU information
- RAM specifications
- Storage drives (with serial numbers, capacity, model)
- Hardware summary
"""

import hashlib
import json
from typing import Any, Dict, List, Optional


def _walk_nodes(raw: Any):
    """
    Generator that walks through all nodes in the lshw JSON tree.
    lshw output is hierarchical with nested 'children' arrays.
    """
    if not isinstance(raw, dict):
        return
    stack = [raw]
    while stack:
        n = stack.pop()
        if not isinstance(n, dict):
            continue
        yield n
        kids = n.get("children")
        if isinstance(kids, list):
            stack.extend(kids)


def _looks_like_serial(s: str) -> bool:
    """
    Check if a string looks like a valid serial number.
    Filters out common placeholder values like "unknown", "0000000", etc.
    """
    if not s:
        return False
    s = s.strip()
    if len(s) < 6:
        return False
    bad = {
        "unknown",
        "none",
        "n/a",
        "na",
        "null",
        "0",
        "0000000",
        "00000000",
        "000000000",
        "not specified",
    }
    return s.lower() not in bad


def extract_serial(raw: dict) -> Optional[str]:
    """
    Extract the device serial number from lshw output.
    Looks at system, motherboard, and chassis serial numbers.
    Returns the first valid serial found.

    Args:
        raw: lshw JSON output (dict)

    Returns:
        Serial number string or None if not found
    """
    candidates: List[str] = []
    if not isinstance(raw, dict):
        return None

    # Check top-level serial and uuid
    for k in ("serial", "uuid"):
        v = raw.get(k)
        if isinstance(v, str) and _looks_like_serial(v):
            candidates.append(v)

    # Walk through all nodes looking for system-level serials
    for n in _walk_nodes(raw):
        cls = n.get("class")
        if cls in ("system", "bus", "motherboard", "bridge", "chassis"):
            v = n.get("serial")
            if isinstance(v, str) and _looks_like_serial(v):
                candidates.append(v)
        if cls == "system":
            v = n.get("uuid")
            if isinstance(v, str) and _looks_like_serial(v):
                candidates.append(v)

    return candidates[0] if candidates else None


def extract_cpu_info(raw: dict) -> Optional[str]:
    """
    Extract CPU information from lshw output.
    Returns a string like "Intel Corp. Intel(R) Core(TM) i5-8350U CPU @ 1.70GHz"

    Args:
        raw: lshw JSON output (dict)

    Returns:
        CPU description string or None if not found
    """
    if not isinstance(raw, dict):
        return None
    for n in _walk_nodes(raw):
        if n.get("class") == "processor":
            product = n.get("product")
            vendor = n.get("vendor")
            if isinstance(product, str) and product.strip():
                if isinstance(vendor, str) and vendor.strip():
                    return f"{vendor} {product}".strip()
                return product.strip()
    return None


def parse_disks(raw: dict) -> List[Dict[str, Any]]:
    """
    Extract all disk drives from lshw output.
    For drives without valid serial numbers, generates a synthetic serial
    based on a hash of the drive characteristics (NOSERIAL-xxxxxxxxxxxxx).

    Args:
        raw: lshw JSON output (dict)

    Returns:
        List of dicts with keys: serial, logicalname, size_bytes, model
    """
    if not isinstance(raw, dict):
        return []

    disks: List[Dict[str, Any]] = []
    for n in _walk_nodes(raw):
        if n.get("class") != "disk":
            continue
        logical = n.get("logicalname")
        size = n.get("size")
        model = n.get("product") or n.get("description")
        serial = n.get("serial")

        if isinstance(serial, str):
            serial = serial.strip()

        # If no valid serial, generate one based on drive characteristics
        if not _looks_like_serial(serial or ""):
            blob = json.dumps(
                {"logical": logical, "size": size, "model": model},
                sort_keys=True,
                default=str,
            ).encode("utf-8", errors="ignore")
            serial = "NOSERIAL-" + hashlib.sha1(blob).hexdigest()[:12]

        disks.append(
            {
                "serial": serial,
                "logicalname": logical,
                "size_bytes": int(size) if isinstance(size, (int, float)) else None,
                "model": model,
            }
        )

    return disks


def format_bytes(num_bytes: int) -> str:
    """
    Convert bytes to human-readable format (KB, MB, GB, TB).

    Args:
        num_bytes: Number of bytes

    Returns:
        Human-readable string like "256.0 GB"
    """
    if not num_bytes:
        return "0 B"

    num = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"


def extract_basic_hw(raw: dict) -> Optional[dict]:
    """
    Extract a basic hardware summary from lshw output.
    Returns RAM and storage information in human-readable format.

    Args:
        raw: lshw JSON output (dict)

    Returns:
        Dict with keys 'ram' and 'storage', or None if no data found
        Example: {"ram": "16.0 GB", "storage": "256.0 GB TOSHIBA THNSFJ25 (SN 95CS1108TBZW)"}
    """
    if not isinstance(raw, dict):
        return None

    result: Dict[str, str] = {}

    # Extract RAM information
    total_bytes = 0
    sysmem = None

    # First, try to find "System Memory" entry (most accurate)
    for n in _walk_nodes(raw):
        if n.get("class") == "memory" and n.get("size"):
            desc = (n.get("description") or "").lower()
            if "system memory" in desc:
                try:
                    sysmem = int(n.get("size"))
                except Exception:
                    pass

    if sysmem:
        total_bytes = sysmem
    else:
        # Fall back to summing all memory (excluding cache)
        for n in _walk_nodes(raw):
            if n.get("class") == "memory" and n.get("size"):
                desc = (n.get("description") or "").lower()
                if "cache" in desc:
                    continue
                try:
                    total_bytes += int(n.get("size"))
                except Exception:
                    pass

    if total_bytes:
        result["ram"] = format_bytes(total_bytes)

    # Extract storage information
    disks = parse_disks(raw)
    if disks:
        labels = []
        for d in disks:
            parts = []
            if d.get("size_bytes"):
                parts.append(format_bytes(d["size_bytes"]))
            if d.get("model"):
                parts.append(d["model"])

            serial = d.get("serial")
            if serial:
                if serial.startswith("NOSERIAL-"):
                    parts.append("(no serial)")
                else:
                    parts.append(f"(SN {serial})")

            labels.append(" ".join(parts))

        result["storage"] = " + ".join(labels)

    return result or None


def parse_lshw_json(data: dict) -> dict:
    """
    Main entry point for parsing lshw JSON.
    Extracts all relevant information into a single summary dict.

    Args:
        data: lshw JSON output (dict)

    Returns:
        Dict with keys: device_serial, cpu_info, hw_summary, disks
    """
    return {
        "device_serial": extract_serial(data),
        "cpu_info": extract_cpu_info(data),
        "hw_summary": extract_basic_hw(data),
        "disks": parse_disks(data),
    }
