// bbr-top: print per-interface traffic rates once a second, from sysfs counters
use std::{env, fs, io, thread, time::Duration};

fn read_counter(iface: &str, name: &str) -> io::Result<u64> {
    let path = format!("/sys/class/net/{iface}/statistics/{name}");
    let text = fs::read_to_string(path)?;
    text.trim()
        .parse::<u64>()
        .map_err(|e| io::Error::new(io::ErrorKind::InvalidData, e))
}

fn main() {
    let ifaces: Vec<String> = env::args().skip(1).collect();
    if ifaces.is_empty() {
        eprintln!("usage: bbr-top <iface> [iface...]");
        std::process::exit(2);
    }

    let mut prev: Vec<(u64, u64)> = ifaces
        .iter()
        .map(|i| (read_counter(i, "rx_bytes").unwrap_or(0), read_counter(i, "tx_bytes").unwrap_or(0)))
        .collect();

    loop {
        thread::sleep(Duration::from_secs(1));
        for (idx, iface) in ifaces.iter().enumerate() {
            let rx = read_counter(iface, "rx_bytes").unwrap_or(0);
            let tx = read_counter(iface, "tx_bytes").unwrap_or(0);
            let (prx, ptx) = prev[idx];
            println!(
                "{iface:<8} rx {:>8.2} Mbit/s  tx {:>8.2} Mbit/s",
                rx.saturating_sub(prx) as f64 * 8.0 / 1e6,
                tx.saturating_sub(ptx) as f64 * 8.0 / 1e6
            );
            prev[idx] = (rx, tx);
        }
        println!();
    }
}

