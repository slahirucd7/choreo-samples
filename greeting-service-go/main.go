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

	// "golang.org/x/net/http2"

)

func main() {

	serverMux := http.NewServeMux()
	serverMux.HandleFunc("/whirpool", getResponse)

	serverPort := 9090
	server := http.Server{
		Addr:    fmt.Sprintf(":%d", serverPort),
		Handler: serverMux,
	}
	go func() {
		log.Printf("Starting HTTP WPServer on port %d\n", serverPort)
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

func getResponse(w http.ResponseWriter, r *http.Request) {

	var token string = ""
	for name, values := range r.Header {
		if name == "Authorization" {
			token = values[0]
		}
	}

	// Load the CA certificate from a file.
	caCert, err := os.ReadFile("/foo/whirpool.pem")
	if err != nil {
		log.Printf("Failed to read CA certificate: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
        return
	}

	// Create a new CA pool and add the server's CA certificate.
	caCertPool := x509.NewCertPool()
	if !caCertPool.AppendCertsFromPEM(caCert) {
		log.Printf("Failed to append CA certificate to pool")
		http.Error(w, "Internal server error", http.StatusInternalServerError)
        return
	}

	req, err := http.NewRequest("GET", "https://ei-latam.whirlpool.com/service-providers/v3.0.0/service-assignment?applianceId=BWL11ABANA&zipCode=04824070", nil)
	if err != nil {
		log.Printf("Failed to create request: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
        return
	}
	req.Header.Set("Authorization", token)


	// Create an HTTP client with custom transport using the TLS config.
	client := &http.Client{
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{
				RootCAs: caCertPool,
			},
			IdleConnTimeout: 120 * time.Second,
		},
		Timeout: 120 * time.Second,
	}

	// Make a GET request to the backend.
	resp, err := client.Do(req)
	if err != nil {
		log.Printf("Failed to make request: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
        return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		log.Printf("Received non-200 response code: %v", resp.StatusCode)
		// Optionally read the body and send it back to the client
		body, _ := io.ReadAll(resp.Body)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(resp.StatusCode)
		w.Write(body)
		return
	}

	// Read and print the response body.
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Printf("Failed to read response body: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
        return
	}

	// log.Printf("Response from backend: %s\n", resp.Body)
	// log.Printf("Response from backend: %d\n", resp.StatusCode)

	// Write the response from the backend to the client.
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, writeErr := w.Write(body)
	if writeErr != nil {
		log.Printf("Failed to write response to client: %v", writeErr)
	}
}