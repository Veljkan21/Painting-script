import json
import subprocess
import sys

def load_bit_set(bit_file):
    with open(bit_file) as f:
        return set(map(int, f.read().strip().replace(",", " ").split()))

def save_bit_set(bit_set, output_file):
    with open(output_file, "w") as f:
        f.write(" ".join(str(b) for b in sorted(bit_set)) + "\n")
    print(f"Final expanded bit set saved to: {output_file}")

def find_top_module(data):
    for mod_name, mod_data in data.get("modules", {}).items():
        if mod_data.get("attributes", {}).get("top") == "00000000000000000000000000000001":
            return mod_name, mod_data
    raise Exception("Top module not found.")

def expand_bits_in_top(json_file_path, bit_set, output_file, all, all_sv):
    with open(json_file_path) as f:
        data = json.load(f)

    top_name, top_module = find_top_module(data)
    cells = top_module.get("cells", {})
    changed = True

    while changed:
        changed = False
        new_bits = set()

        for cell_name, cell in cells.items():
            if "$" not in cell_name:
                print(f"🔍 Found submodule instance: {cell_name} ({cell['type']})")

                port_dirs = cell.get("port_directions", {})
                connections = cell.get("connections", {})

                matching_ports = {
                    port for port, direction in port_dirs.items()
                    if direction == "input" and any(b in bit_set for b in connections.get(port, []))
                }

                if matching_ports:
                    module_type = cell["type"]
                    yosys_command = (
                        f"read_slang --ignore-assertions {all_sv} --top {module_type}; "
                        f"hierarchy -check; setattr -mod -set keep_hierarchy 1; proc; write_json ./json-test/{module_type}.json"
                    )
                    subprocess.run(["yosys", "-m", "slang", "-p", yosys_command], check=True)
                    json_file_name = f"./json-test/{module_type}.json"

                    cmd_all_bits = ["python3", "/home/veljko/Toma/Posao/Toma/Filter-script/all_bits.py", all, json_file_name, module_type, json_input] + list(matching_ports)
                    print("Running:", " ".join(cmd_all_bits))
                    subprocess.run(cmd_all_bits)

                    cmd_all_bits2 = ["python3", "/home/veljko/Toma/Posao/Toma/Filter-script/all_bits2.py", json_file_name, module_type, json_file_path]
                    print("Running:", " ".join(cmd_all_bits2))
                    subprocess.run(cmd_all_bits2)

                    result_file = f"./txt/all_final_{module_type}.txt"
                    try:
                        with open(result_file) as rf:
                            new_mapped = set(map(int, rf.read().strip().split()))
                            before = len(bit_set)
                            bit_set.update(new_mapped)
                            if len(bit_set) > before:
                                changed = True
                    except FileNotFoundError:
                        print(f"Warning: result file {result_file} not found")

                continue  # next cell

            # If primitive cell: propagate bits from inputs to outputs
            port_dirs = cell.get("port_directions", {})
            connections = cell.get("connections", {})

            input_bits = [
                b for port, dir in port_dirs.items()
                if dir == "input" for b in connections.get(port, []) if isinstance(b, int)
            ]

            if any(b in bit_set for b in input_bits):
                for port, direction in port_dirs.items():
                    if direction == "output":
                        output_bits = [b for b in connections.get(port, []) if isinstance(b, int)]
                        for b in output_bits:
                            if b not in bit_set:
                                new_bits.add(b)

        if new_bits:
            bit_set.update(new_bits)
            changed = True

    save_bit_set(bit_set, output_file)

# === USAGE ===
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python all_bits3.py <module_name> <yosys_json_file>")
        sys.exit(1)
    all_sv = sys.argv[1] 
    module_name = sys.argv[2]
    json_input = sys.argv[3]
    all = sys.argv[4]

    input_bits_file = f"./txt/all_final_{module_name}.txt"
    output_file = "all_final.txt"

    initial_bits = load_bit_set(input_bits_file)
    expand_bits_in_top(json_input, initial_bits, output_file,all, all_sv)