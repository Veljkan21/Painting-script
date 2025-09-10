#!/usr/bin/env python3
import json
import sys
import os


def sort_key(x):
    """Sort numbers numerički, stringove abecedno."""
    if isinstance(x, int):
        return (0, x)
    return (1, str(x))


def map_bits_all_instances(module_name, input_bits, module_file_path, top_file_path, output_txt_path):
    # Load local module
    with open(module_file_path) as f:
        module_data = json.load(f)["modules"][module_name]

    # Load top module (e.g. core.json)
    with open(top_file_path) as f:
        top_data = json.load(f)

    # Find top-level module (one with attribute "top" == 1)
    top_module = None
    for mod_name, mod_data in top_data["modules"].items():
        if mod_data.get("attributes", {}).get("top") == "00000000000000000000000000000001":
            top_module = mod_data
            break

    if top_module is None:
        raise Exception("Top module not found in top_file JSON.")

    # Map bit -> port name
    bit_to_port = {}
    for port_name, port_info in module_data["ports"].items():
        for bit in port_info["bits"]:
            bit_to_port[bit] = port_name

    # Collect mapped bits
    mapped_bits = []

    for cell_name, cell in top_module.get("cells", {}).items():
        if cell.get("type") != module_name:
            continue

        for bit in input_bits:
            port = bit_to_port.get(bit)
            if not port:
                continue

            try:
                local_index = module_data["ports"][port]["bits"].index(bit)
                global_bit = cell["connections"][port][local_index]
                mapped_bits.append(global_bit)
            except Exception:
                continue  # skip if mapping fails

    # osiguraj da folder postoji
    os.makedirs(os.path.dirname(output_txt_path), exist_ok=True)

    # Write mapped bits to file
    with open(output_txt_path, "w") as f:
        f.write(" ".join(str(b) for b in sorted(set(mapped_bits), key=sort_key)) + "\n")

    print(f"Mapped bits (from all instances) saved to {output_txt_path}")


# === USAGE ===
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 all_bits2.py <module.json> <module_name> <top.json>")
        sys.exit(1)

    module_file_path = sys.argv[1]
    module_name = sys.argv[2]
    top_file_path = sys.argv[3]

    input_txt_path = f"./txt/final_{module_name}_bits.txt"
    output_txt_path = f"./txt/all_final_{module_name}.txt"

    # učitaj input bits iz fajla
    with open(input_txt_path) as f:
        input_bits = []
        for tok in f.read().strip().split():
            try:
                input_bits.append(int(tok))
            except ValueError:
                input_bits.append(tok)  # ostavi string ako nije broj

    map_bits_all_instances(module_name, input_bits, module_file_path, top_file_path, output_txt_path)
