// 当前乒乓缓存实现
void pingpong_load(int channel) {
    if (ping_busy) {
        // 等ping用完
        wait(ping_done);
    }
    load_to_ping(channel);
    ping_busy = 1;
}

void compute() {
    for (int i = 0; i < 100; i++) {
        pingpong_load(i);  // 这里串行了，应该预取
        process_pong();
    }
}
