#!/bin/sh
wget --cut-dirs=5 -m -nH -P www.phreak.org-virus_l -np http://www.phreak.org/archives/The_Collection/newsletr/virus/virus_l/
find www.phreak.org-virus_l -name index.html -exec rm {} \;
find www.phreak.org-virus_l -name robots.txt -exec rm {} \;
