# ESEF fixtures -- SYNTHETIC

`synthetic_report.xhtml` is a made-up inline-XBRL report of about ten facts for
an invented issuer ("Exempel AB", LEI 5299000000000000EX01). It is not any
company's document and no real issuer document is committed here. The tests
build the report package (ZIP with META-INF/taxonomyPackage.xml) from it at
run time. It covers: scale=6, sign="-", ixt:fixed-zero, a dimensional fact
(scenario, skipped), an extension concept (counted, not read), a comparative
year, comma-decimal display, and an instant (balance-sheet) fact.
