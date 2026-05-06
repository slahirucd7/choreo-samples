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
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

type Student struct {
	ID   string `json:"id"`
	Name string `json:"name"`
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/students/quick", createStudentQuick)
	mux.HandleFunc("/students", createStudent)

	serverVar := http.Server{
		Addr:    fmt.Sprintf(":%d", 8080),
		Handler: mux,
	}
	go func() {
		log.Println("Service starting on :8080")
		if err := serverVar.ListenAndServe(); !errors.Is(err, http.ErrServerClosed) {
			log.Fatalf("ListenAndServe error: %v", err)
		}
	}()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)
	<-stop

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := serverVar.Shutdown(ctx); err != nil {
		log.Fatalf("Shutdown error: %v", err)
	}
}

// createStudentQuick serves the create-students-quick-public endpoint.
// This endpoint deploys successfully and is the one that causes APIM token collision.
func createStudentQuick(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(Student{ID: "quick-001", Name: "Quick Student"})
}

// createStudent serves the create-students-public endpoint.
// This endpoint fails to reconcile with APIM because the Atlas search for
// "create-students-public" tokenizes to [create, students, public] and
// false-matches "create-students-quick-public" which contains all 3 tokens.
func createStudent(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(Student{ID: "001", Name: "New Student"})
}
