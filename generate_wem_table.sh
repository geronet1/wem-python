#!/bin/bash -x

#./wem.py -h | sed 's/\\/\\\\/g;s/^.*$/&\\/g' > ../html/wem.js

./wem.py -h | tr '\n' ' ' > ../html/wem/wem.js

./wem.py -t > ../html/wem-values.html

#;s/'\''/\\'\''/g
