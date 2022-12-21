python3 server.py 9999 &
python3 client.py localhost:9999 file.jpg received-1.jpg &
python3 client.py localhost:9999 file.jpg received-2.jpg &
sleep 3
echo sleep\ for\ 3\ seconds
python3 client.py localhost:9999 file.jpg received-3.jpg &
sleep 5
echo sleep\ for\ 5\ seconds
python3 client.py localhost:9999 file.jpg received-4.jpg &
