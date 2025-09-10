import sys
import subprocess
import json
import shutil
import os

def get_top_module(data):
    for name, mod in data.get("modules", {}).items():
        if mod.get("attributes", {}).get("top") == "00000000000000000000000000000001":
            return name, mod
    return None, None

def write_top_module_bits(module_data, port_names, output_path):
    all_bits = []
    for port in port_names:
        port_data = module_data.get("ports", {}).get(port)
        if port_data:
            all_bits.extend(port_data.get("bits", []))
        else:
            print(f"Warning: port '{port}' not found in top module.")
    with open(output_path, "w") as f:
        f.write(" ".join(map(str, sorted(set(all_bits)))) + "\n")
    print(f"Wrote bits from top module ports {port_names} to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run.py all/one <module_name> top.json all.sv [signal1 signal2 ...]")
        sys.exit(1)
    all = sys.argv[1]
    module_name = sys.argv[2]
    top_json = sys.argv[3]
    all_sv = sys.argv[4]
    signals = sys.argv[5:]
    json_file = f"./json-test/{module_name}.json"

    # Load svi_blackbox.json to check top module
    with open(top_json) as f:
        svi_data = json.load(f)
    module_exists = module_name in svi_data.get("modules", {})

    top_name, top_module = get_top_module(svi_data)
    cmd0 = ["python3", "/home/veljko/Toma/Posao/Toma/Filter-script/all_bits1.py",all_sv, json_file, module_name, top_json] + signals
    print("Running:", " ".join(cmd0))
    subprocess.run(cmd0)

    if not module_exists:
        # === Run detailed_bits.py
        cmd_detailed = ["python3", "/home/veljko/Toma/Posao/Toma/Filter-script/detailed_bits.py", top_json, module_name] + signals
        print("Running:", " ".join(cmd_detailed))
        subprocess.run(cmd_detailed)

    elif module_name == top_name:
        # === If top module: extract bits directly
        output_path = f"./txt/all_final_{module_name}.txt"
        write_top_module_bits(top_module, signals, output_path)
    else:
        # === Step 1: all_bits.py
        cmd1 = ["python3", "/home/veljko/Toma/Posao/Toma/Filter-script/all_bits.py", all, json_file, module_name, top_json] + signals
        print("Running:", " ".join(cmd1))
        subprocess.run(cmd1)

        # === Step 2: all_bits2.py
        cmd2 = ["python3", "/home/veljko/Toma/Posao/Toma/Filter-script/all_bits2.py", json_file, module_name, top_json]
        print("Running:", " ".join(cmd2))
        subprocess.run(cmd2)


    # === Step 3: all_bits3.py
    cmd3 = ["python3", "/home/veljko/Toma/Posao/Toma/Filter-script/all_bits3.py", all_sv, module_name, top_json, all]
    print("Running:", " ".join(cmd3))
    subprocess.run(cmd3)

    # === Step 4: all_bits4.py
    cmd4 = ["python3", "/home/veljko/Toma/Posao/Toma/Filter-script/all_bits4.py", top_json]
    print("Running:", " ".join(cmd4))
    subprocess.run(cmd4)



if os.path.exists("txt") and os.path.isdir("txt"):
    shutil.rmtree("txt")
    print(f"Deleted: txt")
else:
    print(f"Folder txt not exists.")
if os.path.exists("json-test") and os.path.isdir("json-test"):
    shutil.rmtree("json-test")
    print(f"Deleted: json-test")
else:
    print(f"Folder json-test not exists.")

