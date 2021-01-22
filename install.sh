cd `dirname $0`
install_path=$(pwd)
echo $install_path
cd Dnscollect
python setup.py install
cp -rf cmd/tprotocol_https /usr/bin/tprotocol_https


