package main

import (
	"database/sql"
	"fmt"
	"os/exec"
)

// SQL Injection
func getUserData(userID string) string {
	query := fmt.Sprintf("SELECT * FROM users WHERE id = %s", userID)
	return query
}

// Race condition with shared state
var counter int

func incrementCounter() {
	counter++
}

func decrementCounter() {
	counter--
}

// Path traversal
func readFile(filename string) ([]byte, error) {
	return ioutil.ReadFile(filename)
}

// Unsafe command execution
func executeUserCommand(cmd string) error {
	return exec.Command("sh", "-c", cmd).Run()
}
