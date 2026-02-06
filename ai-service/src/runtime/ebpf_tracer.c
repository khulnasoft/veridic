#include <uapi/linux/ptrace.h>
#include <net/sock.h>
#include <bcc/proto.h>

#define ARGSIZE 128
#define SYSCALL_EXECVE 59
#define SYSCALL_OPENAT 257
#define SYSCALL_READ 0
#define SYSCALL_WRITE 1
#define SYSCALL_CONNECT 42

struct syscall_event {
    u32 pid;
    u32 ppid;
    u32 uid;
    u32 gid;
    u64 timestamp_ns;
    u32 syscall_num;
    char syscall_name[16];
    s64 retval;
    int errno;
    char args[4][ARGSIZE];
};

BPF_PERF_OUTPUT(events);
BPF_HASH(pids_to_track, u32, u32);

// Tracepoint: sys_enter_execve
TRACEPOINT_PROBE(syscalls, sys_enter_execve) {
    u64 uid_gid = bpf_get_current_uid_gid();
    u32 uid = uid_gid & 0xFFFFFFFF;
    u32 gid = uid_gid >> 32;
    u32 pid = bpf_get_current_pid_tgid() & 0xFFFFFFFF;
    u32 ppid = ctx->__data_loc_filename >> 16;
    
    struct syscall_event *event = events.ringbuf_reserve(sizeof(*event));
    if (!event) return 0;
    
    event->pid = pid;
    event->ppid = ppid;
    event->uid = uid;
    event->gid = gid;
    event->timestamp_ns = bpf_ktime_get_ns();
    event->syscall_num = SYSCALL_EXECVE;
    __builtin_memcpy(event->syscall_name, "execve", 6);
    
    // Read filename from tracepoint args
    bpf_probe_read_kernel_str(&event->args[0], ARGSIZE, (void *)args->filename);
    
    events.perf_submit(args, event, sizeof(*event));
    return 0;
}

// Tracepoint: sys_enter_openat
TRACEPOINT_PROBE(syscalls, sys_enter_openat) {
    u64 uid_gid = bpf_get_current_uid_gid();
    u32 uid = uid_gid & 0xFFFFFFFF;
    u32 gid = uid_gid >> 32;
    u32 pid = bpf_get_current_pid_tgid() & 0xFFFFFFFF;
    
    struct syscall_event *event = events.ringbuf_reserve(sizeof(*event));
    if (!event) return 0;
    
    event->pid = pid;
    event->uid = uid;
    event->gid = gid;
    event->timestamp_ns = bpf_ktime_get_ns();
    event->syscall_num = SYSCALL_OPENAT;
    __builtin_memcpy(event->syscall_name, "openat", 6);
    
    // Read path and flags
    bpf_probe_read_kernel_str(&event->args[0], ARGSIZE, (void *)args->filename);
    
    events.perf_submit(args, event, sizeof(*event));
    return 0;
}

// Tracepoint: sys_exit_openat
TRACEPOINT_PROBE(syscalls, sys_exit_openat) {
    u32 pid = bpf_get_current_pid_tgid() & 0xFFFFFFFF;
    
    struct syscall_event *event = events.ringbuf_reserve(sizeof(*event));
    if (!event) return 0;
    
    event->pid = pid;
    event->timestamp_ns = bpf_ktime_get_ns();
    event->syscall_num = SYSCALL_OPENAT;
    __builtin_memcpy(event->syscall_name, "openat", 6);
    event->retval = ctx->ret;
    event->errno = (ctx->ret < 0) ? -ctx->ret : 0;
    
    events.perf_submit(args, event, sizeof(*event));
    return 0;
}

// Tracepoint: sys_enter_read
TRACEPOINT_PROBE(syscalls, sys_enter_read) {
    u32 pid = bpf_get_current_pid_tgid() & 0xFFFFFFFF;
    
    struct syscall_event *event = events.ringbuf_reserve(sizeof(*event));
    if (!event) return 0;
    
    event->pid = pid;
    event->timestamp_ns = bpf_ktime_get_ns();
    event->syscall_num = SYSCALL_READ;
    __builtin_memcpy(event->syscall_name, "read", 4);
    event->args[0][0] = 0;
    
    events.perf_submit(args, event, sizeof(*event));
    return 0;
}

// Tracepoint: sys_exit_read
TRACEPOINT_PROBE(syscalls, sys_exit_read) {
    u32 pid = bpf_get_current_pid_tgid() & 0xFFFFFFFF;
    
    struct syscall_event *event = events.ringbuf_reserve(sizeof(*event));
    if (!event) return 0;
    
    event->pid = pid;
    event->timestamp_ns = bpf_ktime_get_ns();
    event->syscall_num = SYSCALL_READ;
    __builtin_memcpy(event->syscall_name, "read", 4);
    event->retval = ctx->ret;
    
    events.perf_submit(args, event, sizeof(*event));
    return 0;
}

// Tracepoint: sys_enter_write
TRACEPOINT_PROBE(syscalls, sys_enter_write) {
    u32 pid = bpf_get_current_pid_tgid() & 0xFFFFFFFF;
    
    struct syscall_event *event = events.ringbuf_reserve(sizeof(*event));
    if (!event) return 0;
    
    event->pid = pid;
    event->timestamp_ns = bpf_ktime_get_ns();
    event->syscall_num = SYSCALL_WRITE;
    __builtin_memcpy(event->syscall_name, "write", 5);
    
    events.perf_submit(args, event, sizeof(*event));
    return 0;
}

// Tracepoint: sys_exit_write
TRACEPOINT_PROBE(syscalls, sys_exit_write) {
    u32 pid = bpf_get_current_pid_tgid() & 0xFFFFFFFF;
    
    struct syscall_event *event = events.ringbuf_reserve(sizeof(*event));
    if (!event) return 0;
    
    event->pid = pid;
    event->timestamp_ns = bpf_ktime_get_ns();
    event->syscall_num = SYSCALL_WRITE;
    __builtin_memcpy(event->syscall_name, "write", 5);
    event->retval = ctx->ret;
    
    events.perf_submit(args, event, sizeof(*event));
    return 0;
}

// Tracepoint: sys_enter_connect
TRACEPOINT_PROBE(syscalls, sys_enter_connect) {
    u32 pid = bpf_get_current_pid_tgid() & 0xFFFFFFFF;
    
    struct syscall_event *event = events.ringbuf_reserve(sizeof(*event));
    if (!event) return 0;
    
    event->pid = pid;
    event->timestamp_ns = bpf_ktime_get_ns();
    event->syscall_num = SYSCALL_CONNECT;
    __builtin_memcpy(event->syscall_name, "connect", 7);
    
    events.perf_submit(args, event, sizeof(*event));
    return 0;
}

// Tracepoint: sys_exit_connect
TRACEPOINT_PROBE(syscalls, sys_exit_connect) {
    u32 pid = bpf_get_current_pid_tgid() & 0xFFFFFFFF;
    
    struct syscall_event *event = events.ringbuf_reserve(sizeof(*event));
    if (!event) return 0;
    
    event->pid = pid;
    event->timestamp_ns = bpf_ktime_get_ns();
    event->syscall_num = SYSCALL_CONNECT;
    __builtin_memcpy(event->syscall_name, "connect", 7);
    event->retval = ctx->ret;
    event->errno = (ctx->ret < 0) ? -ctx->ret : 0;
    
    events.perf_submit(args, event, sizeof(*event));
    return 0;
}
