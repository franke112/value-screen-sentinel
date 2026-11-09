"""Cut a 10-K's cash flow statement out of its inline XBRL, for a fixture.

    .venv/bin/python tests/fixtures/cfrecon/extract.py SOURCE.htm OUT.htm

Keeps the document's contexts and units (no hidden facts) and the tables
from the one holding the statement's net income row to the one holding
its operating cash flow, verbatim but with `style` attributes dropped.
The 10-Ks themselves are in sources/, which is not committed.
"""
import re
import sys
from lxml import etree

NS_IX = "http://www.xbrl.org/2013/inlineXBRL"
NS_XBRLI = "http://www.xbrl.org/2003/instance"
OCF = "us-gaap:NetCashProvidedByUsedInOperatingActivities"
START = ("us-gaap:NetIncomeLoss", "us-gaap:ProfitLoss")


def main(src, out):
    root = etree.fromstring(open(src, "rb").read(),
                            parser=etree.XMLParser(recover=True, huge_tree=True))
    facts = [e for e in root.iter(f"{{{NS_IX}}}nonFraction")
             if not any(a.tag == f"{{{NS_IX}}}header" for a in e.iterancestors())]
    first_ocf = next(i for i, e in enumerate(facts) if e.get("name") == OCF)
    ctx = facts[first_ocf].get("contextRef")
    start = next(i for i in range(first_ocf, -1, -1)
                 if facts[i].get("name") in START and facts[i].get("contextRef") == ctx)

    def table(e):
        return next(a for a in e.iterancestors() if etree.QName(a).localname == "table")

    tables, t = [], table(facts[start])
    end_t = table(facts[first_ocf])
    while True:
        tables.append(t)
        if t is end_t:
            break
        t = t.getnext()
        while t is not None and etree.QName(t).localname != "table":
            t = t.getnext()
        if t is None:
            raise SystemExit("the statement's tables are not siblings; cut by hand")
    contexts = [c for c in root.iter(f"{{{NS_XBRLI}}}context")
                if c.find(f".//{{{NS_XBRLI}}}segment") is None
                and c.find(f".//{{{NS_XBRLI}}}scenario") is None]
    units = [u for u in root.iter(f"{{{NS_XBRLI}}}unit")]
    for el in tables:
        for node in el.iter():
            node.attrib.pop("style", None)
    body = b"".join(etree.tostring(t) for t in tables)
    res = b"".join(etree.tostring(c) for c in contexts + units)
    doc = (b'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:ix="' + NS_IX.encode()
           + b'" xmlns:xbrli="' + NS_XBRLI.encode() + b'"><body><div><ix:header>'
           b'<ix:resources>' + res + b'</ix:resources></ix:header></div>' + body
           + b'</body></html>')
    doc = re.sub(rb' xmlns:\w+="[^"]*"(?=[^<]*>)', b"", doc)  # re-declared below
    doc = doc.replace(b"<html ", b'<html xmlns:ix="' + NS_IX.encode() + b'" xmlns:xbrli="'
                      + NS_XBRLI.encode() + b'" xmlns:ixt="http://www.xbrl.org/inlineXBRL/transformation/2020-02-12" ', 1)
    open(out, "wb").write(doc)


if __name__ == "__main__":
    main(*sys.argv[1:3])
