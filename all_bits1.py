import json
import sys
import os
import subprocess
def collect_input_bits(module_data, port_list):
    input_bits = []
    for port in port_list:
        if port not in module_data["ports"]:
            print(f"Warning: Port '{port}' not found.")
            continue
        port_info = module_data["ports"][port]
        if port_info["direction"] != "input":
            print(f"Warning: Port '{port}' is not an input.")
            continue
        input_bits.extend(port_info["bits"])
    return input_bits

def map_bits_all_instances(module_name, input_bits, module_file_path, top_file_path, output_txt_path):
    # Load local module
    with open(module_file_path) as f:
        module_data = json.load(f)["modules"][module_name]

    # Load top module
    with open(top_file_path) as f:
        top_data = json.load(f)

    # Find top-level module
    top_module = None
    for mod_name, mod_data in top_data["modules"].items():
        if mod_data.get("attributes", {}).get("top") == "00000000000000000000000000000001":
            top_module = mod_data
            break

    if top_module is None:
        raise Exception("Top module not found.")

    # Map bit -> port
    bit_to_port = {}
    for port_name, port_info in module_data["ports"].items():
        for bit in port_info["bits"]:
            bit_to_port[bit] = port_name

    mapped_bits = []
    for name, cell in top_module.get("cells", {}).items():
        if cell["type"] != module_name:
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
                continue

    with open(output_txt_path, "w") as f:
        f.write(" ".join(str(b) for b in sorted(set(mapped_bits))) + "\n")

    print(f"Mapped bits (from all instances) saved to {output_txt_path}")
    return mapped_bits


# === MAIN ===
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python all_bits1.py all.sv <module_json> <module_name> <top_json> <port1> [<port2> ...]")
        sys.exit(1)



    if not os.path.exists("txt"):
        os.makedirs("txt")
    else:
        print(f"Folder txt already exists.")

    if not os.path.exists("json-test"):
        os.makedirs("json-test")
    else:
        print(f"Folder json-test already exists.")

    all_sv = sys.argv[1]
    module_file_path =sys.argv[2]
    module_name = sys.argv[3]
    top_file_path = sys.argv[4]
    port_list = sys.argv[5:]  # <-- signal names (ports) from terminal
    yosys_command = (
                        f"read_slang --ignore-assertions {all_sv} --top {module_name}; "
                        f"hierarchy -check; setattr -mod -set keep_hierarchy 1; proc; write_json ./json-test/{module_name}.json"
                    )
    subprocess.run(["yosys", "-m", "slang", "-p", yosys_command], check=True)
    json_file_name = f"./json-test/{module_name}.json"

    # Load module
    with open(module_file_path) as f:
        module_data = json.load(f)["modules"][module_name]

    # === Step 1: Extract input bits from specified input ports
    local_input_bits = collect_input_bits(module_data, port_list)

    # === Step 2: Save local input bits to input.txt
    with open("./txt/input.txt", "w") as f:
        f.write(" ".join(str(b) for b in sorted(local_input_bits)) + "\n")
    print("Saved local input bits to input.txt")

    # === Step 3: Map them globally (all instances)
    map_bits_all_instances(
        module_name,
        local_input_bits,
        module_file_path,
        top_file_path,
        output_txt_path="./txt/final_input.txt"
    )
