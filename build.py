#!/usr/bin/env python3
"""Build Shadowrocket rulesets from v2fly/domain-list-community (dlc.dat).

Downloads the compiled dlc.dat from the v2fly release branch (jsdelivr mirror),
parses the protobuf with a minimal stdlib-only reader, and emits Shadowrocket
RULE-SET list files into Rulesets/.
"""
import os
import urllib.request

DLC_URL = "https://cdn.jsdelivr.net/gh/v2fly/domain-list-community@release/dlc.dat"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Rulesets")

AI_EXTRA = [
    "DOMAIN-SUFFIX,openai.com", "DOMAIN-SUFFIX,chatgpt.com",
    "DOMAIN-SUFFIX,oaistatic.com", "DOMAIN-SUFFIX,oaiusercontent.com",
    "DOMAIN-SUFFIX,anthropic.com", "DOMAIN-SUFFIX,claude.ai",
    "DOMAIN-SUFFIX,gemini.google.com", "DOMAIN-SUFFIX,aistudio.google.com",
    "DOMAIN-SUFFIX,perplexity.ai", "DOMAIN-SUFFIX,x.ai",
    "DOMAIN-SUFFIX,grok.com", "DOMAIN-SUFFIX,copilot.microsoft.com",
    "DOMAIN-SUFFIX,deepseek.com",
]
PRIVATE_CIDRS = [
    "IP-CIDR,10.0.0.0/8", "IP-CIDR,172.16.0.0/12", "IP-CIDR,192.168.0.0/16",
    "IP-CIDR,127.0.0.0/8", "IP-CIDR,169.254.0.0/16", "IP-CIDR,100.64.0.0/10",
]
TELEGRAM_CIDRS = [
    "IP-CIDR,91.108.4.0/22", "IP-CIDR,91.108.8.0/22", "IP-CIDR,91.108.12.0/22",
    "IP-CIDR,91.108.16.0/22", "IP-CIDR,91.108.56.0/22", "IP-CIDR,149.154.160.0/20",
]
TYPEMAP = {0: "DOMAIN-KEYWORD", 2: "DOMAIN-SUFFIX", 3: "DOMAIN"}


def varint(buf, i):
    shift = 0
    result = 0
    while True:
        b = buf[i]
        i += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, i


def fields(buf):
    i = 0
    while i < len(buf):
        key, i = varint(buf, i)
        num, wt = key >> 3, key & 7
        if wt == 0:
            v, i = varint(buf, i)
            yield num, v
        elif wt == 2:
            ln, i = varint(buf, i)
            yield num, buf[i:i + ln]
            i += ln
        elif wt == 5:
            yield num, buf[i:i + 4]
            i += 4
        elif wt == 1:
            yield num, buf[i:i + 8]
            i += 8
        else:
            raise ValueError(f"bad wire type {wt}")


def parse_dlc(data):
    sites = {}
    for num, entry in fields(data):
        if num != 1:
            continue
        code = None
        domains = []
        for n2, v2 in fields(entry):
            if n2 == 1:
                code = v2.decode()
            elif n2 == 2:
                dtype = None
                dval = None
                for n3, v3 in fields(v2):
                    if n3 == 1:
                        dtype = v3
                    elif n3 == 2:
                        dval = v3.decode()
                domains.append((dtype, dval))
        sites[code] = domains
    return sites


def emit(sites, code, filename, header, extra=()):
    out = set()
    for dtype, dval in sites.get(code, []):
        if dtype in TYPEMAP:
            out.add(f"{TYPEMAP[dtype]},{dval}")
    out.update(extra)
    lines = sorted(out)
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w") as f:
        f.write(header + "\n")
        f.write("\n".join(lines) + "\n")
    print(filename, len(lines))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("downloading", DLC_URL)
    with urllib.request.urlopen(DLC_URL, timeout=120) as r:
        data = r.read()
    print("dlc.dat bytes:", len(data))
    sites = parse_dlc(data)
    emit(sites, "PRIVATE", "Private.list",
         "# Private / LAN (v2fly: private) + IP ranges", PRIVATE_CIDRS)
    emit(sites, "GEOLOCATION-CN", "Direct.list",
         "# Direct (v2fly: geolocation-cn)")
    emit(sites, "GEOLOCATION-!CN", "Proxy.list",
         "# Proxy (v2fly: geolocation-!cn)")
    emit(sites, "TELEGRAM", "Telegram.list",
         "# Telegram (v2fly: telegram) + IP ranges", TELEGRAM_CIDRS)
    emit(sites, "CATEGORY-AI-CHAT-!CN", "AI.list",
         "# AI services (v2fly: category-ai-chat-!cn + core domains)", AI_EXTRA)


if __name__ == "__main__":
    main()
