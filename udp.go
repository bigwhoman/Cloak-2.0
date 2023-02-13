package main

import (
	"fmt"
	"log"
	"net"
)

func main() {
	conn, err := net.ListenUDP("udp", &net.UDPAddr{
		IP:   net.ParseIP("127.0.0.1"),
		Port: 12345,
	})
	if err != nil {
		log.Fatalln("listen:", err)
		return
	}
	for {
		var buffer [1500]byte
		rlen, remote, err := conn.ReadFromUDP(buffer[:])
		if err != nil {
			log.Fatalln("read:", err)
		}
		fmt.Println(string(buffer[:rlen]), "from", remote.String())
	}
}
