// Unsafe pointer dereference
fn unsafe_pointer_deref() {
    let x = 5;
    let ptr = &x as *const i32;
    unsafe {
        println!("{}", *ptr);
    }
}

// Unsafe buffer overflow potential
fn unsafe_string_ops(user_input: String) {
    let buffer: [u8; 10] = [0; 10];
    let input_bytes = user_input.as_bytes();
    unsafe {
        // Potential buffer overflow if input_bytes.len() > 10
        std::ptr::copy_nonoverlapping(
            input_bytes.as_ptr(),
            buffer.as_ptr() as *mut u8,
            input_bytes.len(),
        );
    }
}

// Panic on user input without validation
fn panic_on_input(index: usize, vec: Vec<i32>) {
    println!("{}", vec[index]); // Panics if index out of bounds
}

// Race condition
use std::sync::{Arc, Mutex};
use std::thread;

fn race_condition() {
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];
    
    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            let mut num = counter.lock().unwrap();
            *num += 1;
        });
        handles.push(handle);
    }
}
