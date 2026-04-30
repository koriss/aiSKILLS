#!/usr/bin/env python3
from pathlib import Path
import argparse,re,sys
BAD=[r"how to\s+(manipulate|persuade|target)",r"optimi[sz]e\s+(propaganda|persuasion|influence)",r"target audience.*message.*to maximize",r"conduct\s+(psyops|psychological operations)",r"разработ(ай|ать).*(кампани[юи]).*(воздейств|пропаганд)",r"как\s+(манипулировать|убедить|воздействовать)"]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("text_file"); args=ap.parse_args()
    txt=Path(args.text_file).read_text(encoding="utf-8",errors="replace"); hits=[p for p in BAD if re.search(p,txt,re.I|re.S)]
    if hits:
        print("operational influence output patterns found:\n"+"\n".join(hits),file=sys.stderr); return 1
    print("OK: no operational IO output detected"); return 0
if __name__=="__main__": raise SystemExit(main())
