

echo "fmt:./start.sh 127.0.0.1 27017"

host = $1
port = $2

echo $port
echo $host

if [ $host = "" -o $port = "" ]
  then
     "echo invalid para"
  else
     nohup dns_scheduler -m $host -p $port >/etc/nul 2>&1 &
     "echo start success"
fi

