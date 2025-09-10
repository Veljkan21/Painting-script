#!/usr/bin/env python3
import json
import sys
import os
from collections import deque


def sort_key(x):
    """Sort numbers numerički, stringove abecedno."""
    if isinstance(x, int):
        return (0, x)
    return (1, str(x))


def extract_connected_bits_with_cells(module_data, port_names, all="one"):
    # --- 0) Port bit -> port name
    bit_to_port = {}
    for port_name, port_info in module_data.get("ports", {}).items():
        for bit in port_info.get("bits", []):
            bit_to_port[bit] = port_name

    # --- 1) Net indeks: bit -> net_id i net_id -> bits
    net_id_of_bit = {}
    net_bits = []
    for bits in (ni.get("bits", []) for ni in module_data.get("netnames", {}).values()):
        if not bits:
            continue
        net_idx = len(net_bits)
        net_bits.append(bits)
        for b in bits:
            net_id_of_bit[b] = net_idx

    # --- 2) Precompute cell fanout by *input bit*
    # samo ćelije čiji type počinje sa "$" (Yosys primitiva)
    cell_fanout = {}  # bit -> list(out_bits)
    for cell_data in module_data.get("cells", {}).values():
        ctype = str(cell_data.get("type", ""))
        if not ctype.startswith("$"):
            continue
        port_dirs = cell_data.get("port_directions", {})
        conns = cell_data.get("connections", {})

        in_bits = set()
        for p, d in port_dirs.items():
            if d == "input":
                in_bits.update(conns.get(p, []))

        out_bits = []
        for p, d in port_dirs.items():
            if d == "output":
                out_bits.extend(conns.get(p, []))

        if not in_bits or not out_bits:
            continue

        for b in in_bits:
            cell_fanout.setdefault(b, []).extend(out_bits)

    # --- 3) BFS seed: svi bitovi iz zadanih portova
    start_bits = []
    for port in port_names:
        start_bits.extend(module_data.get("ports", {}).get(port, {}).get("bits", []))

    final_bits_set = set(start_bits)
    queue = deque(start_bits)

    # da ne ubacujemo isti net više puta
    expanded_nets = set()

    max_iterations = 5_000_000
    iterations = 0

    while queue and iterations < max_iterations:
        iterations += 1
        b = queue.popleft()

        # 3a) proširi preko netname-a: ubaci sve bitove njegovog neta jednom
        nid = net_id_of_bit.get(b, None)
        if nid is not None and nid not in expanded_nets:
            expanded_nets.add(nid)
            for nb in net_bits[nid]:
                if nb not in final_bits_set:
                    final_bits_set.add(nb)
                    queue.append(nb)

        # 3b) proširi preko logičkih ćelija: ulazni bit -> svi izlazni bitovi
        for ob in cell_fanout.get(b, []):
            if ob not in final_bits_set:
                final_bits_set.add(ob)
                queue.append(ob)

        if iterations % 100_000 == 0:
            # mali heartbeat da znaš da “diše” na velikim dizajnima
            print(f"[trace] visited={len(final_bits_set)} queue={len(queue)}")

    if iterations >= max_iterations:
        print(f"WARNING: Reached iteration cap ({max_iterations}). Result may be incomplete.")

    # --- 4) Mapiranje nazad u portove (po potrebi filtriraj na output)
    final_ports = {}
    for bit in sorted(final_bits_set, key=sort_key):
        port = bit_to_port.get(bit)
        if not port:
            continue
        if all != "all":
            if module_data["ports"][port]["direction"] != "output":
                continue
        final_ports.setdefault(port, []).append(bit)

    return sorted(final_bits_set, key=sort_key), final_ports



def main(module_file_path, module_name, port_list, output_txt_path, all,
         output_txt_path2):
    with open(module_file_path) as f:
        data = json.load(f)

    module_data = data["modules"][module_name]
    final_bits, final_ports = extract_connected_bits_with_cells(module_data, port_list, all)

    # osiguraj da folder postoji
    os.makedirs(os.path.dirname(output_txt_path), exist_ok=True)

    with open(output_txt_path, "w") as f:
        for port, bits in final_ports.items():
            f.write(" ".join(str(bit) for bit in sorted(bits, key=sort_key)) + " ")

    with open(output_txt_path2, "w") as f:
        f.write(" ".join(str(bit) for bit in sorted(final_bits, key=sort_key)) + "\n\n")


    print(f"Saved to: {output_txt_path}")
    print(f"Saved to: {output_txt_path2}")


# === MAIN ===
if __name__ == "__main__":
    all = sys.argv[1]
    module_file_path = sys.argv[2]
    module_name = sys.argv[3]
    top_json = sys.argv[4]     # trenutno se ne koristi
    port_list = sys.argv[5:]

    output_txt_path = f"./txt/final_{module_name}_bits.txt"
    output_txt_path2 = f"./txt/final_intern_{module_name}_bits.txt"

    main(module_file_path, module_name, port_list, output_txt_path, all,
         output_txt_path2)
