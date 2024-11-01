/*
 * Copyright (c) 2023, WSO2 LLC. (https://www.wso2.com/) All Rights Reserved.
 *
 * WSO2 LLC. licenses this file to you under the Apache License,
 * Version 2.0 (the "License"); you may not use this file except
 * in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

package main

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"errors"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {

	serverMux := http.NewServeMux()
	serverMux.HandleFunc("/whirpool", greet)

	serverPort := 9090
	server := http.Server{
		Addr:    fmt.Sprintf(":%d", serverPort),
		Handler: serverMux,
	}
	go func() {
		log.Printf("Starting HTTP Greeter on port %d\n", serverPort)
		if err := server.ListenAndServe(); !errors.Is(err, http.ErrServerClosed) {
			log.Fatalf("HTTP ListenAndServe error: %v", err)
		}
		log.Println("HTTP server stopped serving new requests.")
	}()

	stopCh := make(chan os.Signal, 1)
	signal.Notify(stopCh, syscall.SIGINT, syscall.SIGTERM)
	<-stopCh // Wait for shutdown signal

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	log.Println("Shutting down the server...")
	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Fatalf("HTTP shutdown error: %v", err)
	}
	log.Println("Shutdown complete.")
}

func greet(w http.ResponseWriter, r *http.Request) {

	// Log request headers
	log.Println("Request Headers:")
	for name, values := range r.Header {
		// Loop over all values for the name
		for _, value := range values {
			log.Printf("%s: %s\n", name, value)
		}
	}


	// Load the CA certificate from a file.
	caCert, err := os.ReadFile("/foo/whirpool.pem")
	if err != nil {
		log.Fatalf("Failed to read CA certificate: %v", err)
	}

	// Create a new CA pool and add the server's CA certificate.
	caCertPool := x509.NewCertPool()
	if !caCertPool.AppendCertsFromPEM(caCert) {
		log.Fatal("Failed to append CA certificate to pool")
	}

	// Configure TLS settings with the CA pool.
	tlsConfig := &tls.Config{
		RootCAs: caCertPool,
	}


	token := os.Getenv("TOKEN")
	req, err := http.NewRequest("GET", "https://ei-latam.whirlpool.com/service-providers/v3.0.0/service-assignment?applianceId=BWL11ABANA&zipCode=04824070", nil)
	if err != nil {
		log.Fatalf("Failed to create request: %v", err)
	}
	req.Header.Set("Authorization", "basic "+token)


	// Create an HTTP client with custom transport using the TLS config.
	client := &http.Client{
		Transport: &http.Transport{
			TLSClientConfig: tlsConfig,
		},
	}

	// Make a GET request to the backend.
	resp, err := client.Do(req)
	if err != nil {
		log.Fatalf("Failed to make request: %v", err)
	}

	// Read and print the response body.
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Fatalf("Failed to read response body: %v", err)
	}

	log.Printf("Response from backend: %s\n", resp.Body)
	log.Printf("Response from backend: %d\n", resp.StatusCode)

	// Write the response from the backend to the client.
	w.Header().Set("Content-Type", "text/plain")
	w.WriteHeader(http.StatusOK)
	_, writeErr := w.Write(body)
	if writeErr != nil {
		log.Printf("Failed to write response to client: %v", writeErr)
	}
	defer resp.Body.Close()
}





// // Specify the directory path
// dirPath := "/foo"

// // Read the contents of the directory
// files, err := os.ReadDir(dirPath)
// if err != nil {
// 	log.Fatalf("Error reading directory: %v", err)
// }

// // List the files
// for _, file := range files {
// 	fmt.Println(file.Name())
// }
// // name := r.URL.Query().Get("name")
// // if name == "" {
// // 	name = "Stranger"
// // }
// // fmt.Fprintf(w, "Hello, %s!\n", name)
