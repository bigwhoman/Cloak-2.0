package main

import (
	"crypto/tls"
	"log"
)

func main() {
	conn, err := tls.Dial("tcp", "127.0.0.1:44443", &tls.Config{InsecureSkipVerify: true})
	if err != nil {
		log.Fatalln("cannot dial:", err)
	}
	defer conn.Close()
	conn.Write([]byte("127.0.0.1:12345"))
	conn.Write([]byte("hello world!"))
	var buffer [32 * 1024]byte
	n, err := conn.Read(buffer[:])
	log.Println(string(buffer[:n]))
}
