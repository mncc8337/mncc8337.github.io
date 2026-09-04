import serial
import sys
import time
import struct

# Default options
options = {
    "source": "benchmark",
    "extract": None,
    "start_addr": 0xBD000000,
}

if len(sys.argv) < 2:
    print("Error: Port was not given.")
    print("Usage:")
    print("  Write:   python3 ser.py <port> <bytes> [--source <file_or_benchmark>]")
    print("  Extract: python3 ser.py <port> <bytes> --extract <output_file>")
    sys.exit(1)

port = sys.argv[1]
size = int(sys.argv[2], 0)

args = sys.argv[3:]
i = 0
while i < len(args):
    if args[i] == "--source":
        options["source"] = args[i + 1]
        i += 1
    elif args[i] == "--extract":
        options["extract"] = args[i + 1]
        i += 1
    i += 1


def read_until_prompt(ser):
    """Reads from serial until the bootloader prompt is found."""
    resp = b""
    while b"<RTL867X>" not in resp:
        byte = ser.read(1)
        if not byte:
            break
        resp += byte
    # Strictly returning raw data, stripped of trailing whitespace, no \n replacement
    return resp.decode(errors="ignore").strip()


def read_word(ser, addr):
    """Uses the 'r' command to read a 4-byte word from the specified address."""
    addr_str = f"0x{addr:08X}"
    cmd = f"r {addr_str}\r".encode()
    print(">", cmd)
    ser.write(cmd)
    resp = read_until_prompt(ser)

    for line in resp.split("\r"):
        line = line.strip()
        # Look for the exact 8-character hex string response
        if len(line) == 8 and all(c in "0123456789abcdefABCDEF" for c in line):
            return bytes.fromhex(line)

    print(f"Error: Failed to read word at {addr_str}. Output: {resp}")
    sys.exit(1)


def extract_memory(ser, start_addr, extract_size):
    """Uses the 'd' command to bulk-dump memory from the router."""
    start_addr_str = f"0x{start_addr:08X}"
    size_str = f"0x{extract_size:x}"
    cmd = f"d {start_addr_str} {size_str}\r".encode()
    print(">", cmd)
    ser.write(cmd)

    extracted_data = bytearray()
    buffer = b""

    while True:
        byte = ser.read(1)
        if not byte:
            break
        buffer += byte

        if b"\r" in buffer:
            line = buffer.decode(errors="ignore").strip()
            buffer = b""

            if "<RTL867X>" in line:
                break

            if ": " in line and line.startswith("0x"):
                hex_section = line.split(": ")[1]
                tokens = hex_section.split()
                for t in tokens:
                    if len(t) == 2 and all(c in "0123456789abcdefABCDEF" for c in t):
                        extracted_data.append(int(t, 16))

    # The 'd' command pads to 16-byte boundaries. Trim the excess.
    return extracted_data[:extract_size]


# Connect and execute
with serial.Serial(port, 115200, timeout=1) as ser:
    # ==========================================
    # MODE 1: EXTRACT USING 'd' COMMAND
    # ==========================================
    if options["extract"]:
        print(f"\n--- Extracting {size} bytes to {options['extract']} ---")
        start_time = time.time()

        extracted_data = extract_memory(ser, options['start_addr'], size)

        with open(options["extract"], "wb") as f:
            f.write(extracted_data)

        elapsed = time.time() - start_time
        print(f"Extraction Complete!")
        print(f"Total Bytes Saved : {len(extracted_data)} bytes")
        print(f"Total Time Elapsed: {elapsed:.2f} seconds")
        if elapsed > 0:
            print(f"Effective Speed   : {(len(extracted_data) / elapsed):.2f} bytes/sec")
        sys.exit(0)

    # ==========================================
    # MODE 2: WRITE / BENCHMARK
    # ==========================================
    data = b""
    if options["source"] == "benchmark":
        print(f"\n--- Safe Benchmark Mode ({size} bytes) ---")
        print("Script will bulk read existing memory via 'd' command, then rewrite it via 'w' to test pure write speed.")
        # Load the target memory into the buffer all at once
        data = bytes(extract_memory(ser, options["start_addr"], size))
    else:
        print(f"\n--- Write Mode ({size} bytes from {options['source']}) ---")
        try:
            with open(options["source"], "rb") as f:
                data = f.read(size if size > 0 else -1)
        except FileNotFoundError:
            print(f"Error: Could not find file {options['source']}")
            sys.exit(1)

    # Real-time Alignment via Memory Read (Applies to both modes just in case)
    if len(data) % 4 != 0:
        aligned_size = (len(data) // 4) * 4
        remainder = len(data) % 4
        last_addr = options["start_addr"] + aligned_size

        print(f"Payload not 4-byte aligned. Reading router memory at 0x{last_addr:08X} to safely pad...")
        existing_word = read_word(ser, last_addr)

        # Splice our trailing bytes with the existing memory bytes
        padded_word = data[aligned_size:] + existing_word[remainder:]
        data = data[:aligned_size] + padded_word
        print("Alignment secure.")

    print("\nStarting write loop...")
    bytes_written = 0
    start_time = time.time()

    loop_size = len(data)

    for i in range(0, loop_size, 4):
        addr = options["start_addr"] + i
        chunk = data[i : i + 4]
        val = struct.unpack(">I", chunk)[0]

        # Force 8-character hex strings with leading zeros
        addr_str = f"0x{addr:08X}"
        val_str = f"0x{val:08X}"

        # Execute Write
        cmd = f"w {addr_str} {val_str}\r".encode()
        # print(">", cmd)

        ser.write(cmd)
        resp = read_until_prompt(ser)

        # Verify Write Format
        # Expected: set 0xbd000000 to 0x100000ff
        expected_ack = f"set {addr_str.lower()} to {hex(val).lower()}"
        if expected_ack not in resp.lower():
            print(f"\nCRITICAL ERROR: Write verification failed at {addr_str}!")
            print(f"Expected: {expected_ack}")
            print(f"Received: {resp}")
            sys.exit(1)

        bytes_written += 4

        # Simple progress indicator for long writes
        if bytes_written % 1024 == 0:
            print(f"Written: {bytes_written} / {loop_size} bytes...", end="\r")

    end_time = time.time()
    elapsed = end_time - start_time

    print("\n\n--- Write Benchmark Complete ---")
    print(f"Total Bytes Written : {bytes_written} bytes")
    print(f"Total Time Elapsed  : {elapsed:.2f} seconds")
    if elapsed > 0:
        print(f"Effective Bandwidth : {(bytes_written / elapsed):.2f} bytes/sec")
