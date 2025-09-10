import json
import sys
import os

def find_top_module(data):
    for mod_name, mod_data in data["modules"].items():
        if mod_data.get("attributes", {}).get("top") == "00000000000000000000000000000001":
            return mod_data
    raise Exception("Top module not found.")

def extract_bits_from_netnames(module_data, target_signals):
    bits = set()
    for netname, netinfo in module_data.get("netnames", {}).items():
        for signal in target_signals:
            if netname.endswith(f".{signal}"):
                bits.update(netinfo["bits"])
    return sorted(bits)

def main(json_path, signal_names, module_name):
    with open(json_path) as f:
        data = json.load(f)

    top_module = find_top_module(data)
    bits = extract_bits_from_netnames(top_module, signal_names)

    os.makedirs("./txt", exist_ok=True)

    # 1. Write to final_input.txt
    with open("./txt/final_input.txt", "w") as f:
        f.write(" ".join(map(str, bits)) + "\n")

    # 2. Write to all_final_{module_name}.txt
    all_final_path = f"./txt/all_final_{module_name}.txt"
    with open(all_final_path, "w") as f:
        f.write(" ".join(map(str, bits)) + "\n")

    print(f"Found {len(bits)} bits for signals {signal_names}")
    print(f"Written to ./txt/final_input.txt and {all_final_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python extract_netname_bits.py <json_path> <signal1> [<signal2> ...]")
        sys.exit(1)

    json_path = sys.argv[1]
    module_name = sys.argv[2]
    signal_names = sys.argv[3:]

    main(json_path, signal_names, module_name)
