package main

import (
	"crypto/tls"
	log "github.com/sirupsen/logrus"
	"io"
	"net"
	"os"
	"sync"
)

func main() {
	// At first, create a TLS server
	// To do so, we need certs
	cer, err := tls.LoadX509KeyPair(os.Getenv("CERT"), os.Getenv("KEY"))
	if err != nil {
		log.WithError(err).Fatalln("cannot load cert and key")
		return
	}
	// Next, we create the server
	ln, err := tls.Listen("tcp", os.Getenv("LISTEN"), &tls.Config{Certificates: []tls.Certificate{cer}})
	if err != nil {
		log.Println(err)
		return
	}
	defer ln.Close()
	// Now wait for connections
	for {
		conn, err := ln.Accept()
		if err != nil {
			log.WithError(err).Error("cannot accept connection")
			break
		}
		go handleConnection(conn)
	}
}

func handleConnection(conn net.Conn) {
	defer conn.Close()
	// 8kb buffer. More than MTU.
	var buffer [8 * 1024]byte
	// We know that the first packet is the destination address
	n, err := conn.Read(buffer[:])
	if err != nil {
		log.WithError(err).WithField("remote", conn.RemoteAddr()).Error("cannot read the first packet")
		return
	}
	// Dial the udp destination
	proxy, err := net.Dial("udp", string(buffer[:n]))
	if err != nil {
		log.WithError(err).WithField("destination", string(buffer[:n])).Error("cannot dial destination")
		return
	}
	defer proxy.Close()
	// Proxy!
	wg := new(sync.WaitGroup)
	wg.Add(2)
	go proxyConnection(proxy, conn, wg)
	go proxyConnection(conn, proxy, wg)
	wg.Wait()
}

func proxyConnection(w io.Writer, r io.Reader, wg *sync.WaitGroup) {
	defer wg.Done()
	_, _ = io.Copy(w, r)
}