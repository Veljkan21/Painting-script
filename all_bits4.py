import json
import sys

def load_bit_set(bit_file):
    with open(bit_file) as f:
        return set(map(int, f.read().strip().replace(",", " ").split()))

def find_top_module(data):
    for mod_name, mod_data in data.get("modules", {}).items():
        if mod_data.get("attributes", {}).get("top") == "00000000000000000000000000000001":
            return mod_name, mod_data
    raise Exception("Top module not found.")

def prune_top_module(json_file_path, bit_set, output_file_path):
    with open(json_file_path) as f:
        data = json.load(f)

    # Dynamically detect top module
    top_name, top_module = find_top_module(data)

    # === Clean cells ===
    new_cells = {}
    for cell_name, cell in top_module.get("cells", {}).items():
        new_conn = {}
        for port, bits in cell.get("connections", {}).items():
            filtered = [b for b in bits if isinstance(b, int) and b in bit_set]
            if filtered:
                new_conn[port] = filtered
        if new_conn:
            cell["connections"] = new_conn
            new_cells[cell_name] = cell
    top_module["cells"] = new_cells

    # === Clean netnames ===
    top_module["netnames"] = {
        name: net for name, net in top_module.get("netnames", {}).items()
        if any(b in bit_set for b in net.get("bits", []))
    }

    # === Clean ports ===
    top_module["ports"] = {
        name: port for name, port in top_module.get("ports", {}).items()
        if any(b in bit_set for b in port.get("bits", []))
    }

    # Save updated top module
    data["modules"][top_name] = top_module

    with open(output_file_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Pruned top module '{top_name}' saved to: {output_file_path}")


# === Entry point ===
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python prune_top_module.py <yosys_json_file>")
        sys.exit(1)
    with open("./txt/final_input.txt", "r") as fin:
        new_data = fin.read().strip()

    with open("all_final.txt", "a") as fout:
        fout.write(new_data + "\n")

    bit_file = "all_final.txt"     # Expected to exist in current dir
    json_input = sys.argv[1]       # Input Yosys JSON
    json_output = "final.json"     # Output pruned file

    keep_bits = load_bit_set(bit_file)
    prune_top_module(json_input, keep_bits, json_output)
