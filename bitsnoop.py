#!/usr/bin/env python3

import pyshark
from pyshark.packet.packet import Packet
from magic import Magic
import sys
import os

GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def log_status(message: str) -> None:
    print(f"{BLUE}[-]{RESET} {message}")


def log_found(ip_pair: tuple, file_type: str) -> None:
    src_ip, dst_ip = ip_pair
    print(f"{GREEN}[+]{RESET} Found: {src_ip} -> {dst_ip:<15} Type: {file_type}")


class BTBucket:
    def __init__(self, pcap: str) -> None:
        self._files = {}
        log_status(f"Reading {pcap}...")
        self._load_pcap(pcap)
        self._extract()
        self._write_files()

    class _Packet:
        def __init__(self, pkt: Packet) -> None:
            self.srca = pkt.ip.addr
            self.srcp = pkt.tcp.port
            self.dsta = pkt.ip.dst
            self.dstp = pkt.tcp.dstport
            self.mapping = f"{self.srca}:{self.srcp}:{self.dsta}:{self.dstp}"
            self.idx = int(pkt.bittorrent.piece_index, 16)
            self.begin = int(pkt.bittorrent.piece_begin, 16)
            self.data = bytes.fromhex(pkt.bittorrent.piece_data.replace(":", ""))
            self.length = len(self.data)

    def _load_pcap(self, pcap: str) -> None:
        try:
            with pyshark.FileCapture(
                pcap, display_filter="bittorrent", keep_packets=False
            ) as cap:
                for idx, pkt in enumerate(cap):
                    print(
                        f"\r{BLUE}[-]{RESET} Packets processed: {idx}",
                        end="",
                        flush=True,
                    )
                    if "piece_data" in pkt.bittorrent.field_names:
                        self._store(pkt)
                print()
        except Exception as e:
            raise RuntimeError(
                f"ERROR Something terribly wrong has happened, are you sure the packet capture is using BitTorrent?\n{e}"
            )

    def _store(self, pkt) -> None:
        pkt = self._Packet(pkt)
        mapping = pkt.mapping
        if mapping not in self._files:
            self._files[mapping] = []

        idx = pkt.idx
        while len(self._files[mapping]) <= idx:
            self._files[mapping].append([])
        self._files[mapping][idx].append(pkt)

    def _extract(self) -> None:
        for mapping, file in self._files.items():
            for idx, part in enumerate(file):
                file[idx] = sorted(part, key=lambda x: x.begin)
                file[idx] = b"".join([i.data for i in file[idx]])
            self._files[mapping] = {"data": b"".join(file)}
            self._files[mapping]["type"] = Magic(True).from_buffer(
                self._files[mapping]["data"]
            )

    def _write_files(self) -> None:
        for k, v in self._files.items():
            srca, srcp, dsta, dstp = k.split(":")
            ftype = v["type"].split("/")[-1] if "/" in v["type"] else "UNK"
            log_found((f"{srca}:{srcp}", f"{dsta}:{dstp}"), ftype)
            with open(f"{k}.{ftype}", "wb") as f:
                f.write(v["data"])


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <pcap_file>")
    pcap = sys.argv[1]
    if not os.path.isfile(pcap):
        raise RuntimeError(f"File not found: {pcap}")
    bucket = BTBucket(pcap)
